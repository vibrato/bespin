import logging

log = logging.getLogger("bespin.amazon.ec2")

def get_instances_in_asg_by_lifecycle_state(credentials, asg_physical_id, lifecycle_state=None):
    instances = []

    asg = credentials.autoscale.get_all_groups(names=[asg_physical_id])
    for instance in asg[0].instances:
        if lifecycle_state is None or lifecycle_state == instance.lifecycle_state:
            instances.append(instance.instance_id)

    return instances

def resume_processes(credentials, asg_physical_id):
    credentials.autoscale.suspend_processes(asg_physical_id, ["ScheduledActions"])

def suspend_processes(credentials, asg_physical_id):
    credentials.autoscale.suspend_processes(asg_physical_id, ["ScheduledActions"])