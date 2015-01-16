from bespin.errors import StackDoesntExist, BadStack
from bespin.amazon.mixin import AmazonMixin
from bespin import helpers as hp

import boto.cloudformation
import logging
import json
import six

log = logging.getLogger("bespin.amazon.cloudformation")

class StatusMeta(object):
    def __new__(cls, name, bases, attrs):
        attrs["name"] = name
        attrs["failed"] = name.endswith("FAILED")
        attrs["complete"] = name.endswith("COMPLETE")
        attrs["in_progress"] = name.endswith("IN_PROGRESS")
        attrs["cleanup_in_progress"] = name.endswith("CLEANUP_IN_PROGRESS")

        attrs["is_create"] = name.startswith("CREATE")
        attrs["is_delete"] = name.startswith("DELETE")
        attrs["is_update"] = name.startswith("UPDATE") and not name.startswith("UPDATE_ROLLBACK")
        attrs["is_rollback"] = name.startswith("ROLLBACK") or name.startswith("UPDATE_ROLLBACK")
        return type(name, bases, attrs)

class Status(object):
    exists = True
    statuses = {}

    @classmethod
    def find(kls, name):
        if name in kls.statuses:
            return kls.statuses[name]
        return six.add_metaclass(StatusMeta)(type(name, (Status, ), {}))

class NONEXISTANT(Status):
    exists = False

class CREATE_IN_PROGRESS(Status): pass
class CREATE_FAILED(Status): pass
class CREATE_COMPLETE(Status): pass

class ROLLBACK_IN_PROGRESS(Status): pass
class ROLLBACK_FAILED(Status): pass
class ROLLBACK_COMPLETE(Status): pass

class DELETE_IN_PROGRESS(Status): pass
class DELETE_FAILED(Status): pass
class DELETE_COMPLETE(Status): pass

class UPDATE_IN_PROGRESS(Status): pass
class UPDATE_COMPLETE_CLEANUP_IN_PROGRESS(Status): pass
class UPDATE_COMPLETE(Status): pass
class UPDATE_ROLLBACK_IN_PROGRESS(Status): pass
class UPDATE_ROLLBACK_FAILED(Status): pass
class UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS(Status): pass
class UPDATE_ROLLBACK_COMPLETE(Status): pass

for kls in [Status] + Status.__subclasses__():
    with_meta = six.add_metaclass(StatusMeta)(kls)
    locals()[kls.__name__] = with_meta
    Status.statuses[kls.__name__] = with_meta

class Cloudformation(AmazonMixin):
    def __init__(self, stack_name, region):
        self.region = region
        self.stack_name = stack_name

    @hp.memoized_property
    def conn(self):
        return boto.cloudformation.connect_to_region(self.region)

    def description(self, force=False):
        """Get the descriptions for the stack"""
        if not getattr(self, "_description", None) or force:
            with self.catch_boto_400(StackDoesntExist, "Couldn't find stack"):
                self._description = self.conn.describe_stacks(self.stack_name)[0]
        return self._description

    @property
    def outputs(self):
        description = self.description()
        if description is None:
            return {}
        else:
            return dict((out.key, out.value) for out in description.outputs)

    @property
    def status(self):
        try:
            description = self.description(force=True)
            return Status.find(description.stack_status)
        except StackDoesntExist:
            return NONEXISTANT

    def map_logical_to_physical_resource_id(self, logical_id):
        resource = self.conn.describe_stack_resource(stack_name_or_id=self.stack_name, logical_resource_id=logical_id)
        return resource['DescribeStackResourceResponse']['DescribeStackResourceResult']['StackResourceDetail']["PhysicalResourceId"]

    def create(self, stack, params, tags):
        log.info("Creating stack (%s)\ttags=%s", self.stack_name, tags)
        params = [(param["ParameterKey"], param["ParameterValue"]) for param in params] if params else None
        self.conn.create_stack(self.stack_name, template_body=json.dumps(stack), parameters=params, tags=tags, capabilities=['CAPABILITY_IAM'])

    def update(self, stack, params):
        log.info("Updating stack (%s)", self.stack_name)
        params = [(param["ParameterKey"], param["ParameterValue"]) for param in params] if params else None
        with self.catch_boto_400(BadStack, "Couldn't update the stack", stack_name=self.stack_name):
            try:
                self.conn.update_stack(self.stack_name, template_body=json.dumps(stack), parameters=params, capabilities=['CAPABILITY_IAM'])
            except boto.exception.BotoServerError as error:
                if error.message == "No updates are to be performed.":
                    log.info("No updates were necessary!")
                else:
                    raise

    def wait(self, timeout=1200):
        status = self.status
        if status.failed:
            raise BadStack("Stack is in a failed state, it must be deleted first", name=self.stack_name, status=status)

        for _ in hp.until(timeout, step=15):
            log.info("Waiting for %s - %s", self.stack_name, status.name)
            if status.exists and not status.complete:
                status = self.status
            else:
                break

        return status

