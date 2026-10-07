"""Resource admission after the user's cancellation of project allocation caps."""


def admit(policy, *, disk_free_bytes, remaining_output_bytes):
    if policy.get('disk_usage_mode') != 'ACTUAL_CAPACITY_ONLY':
        raise ValueError('current explicit unlimited-allocation policy required')
    for value in (disk_free_bytes, remaining_output_bytes):
        if type(value) is not int or value < 0:
            raise ValueError('actual free disk and remaining writes must be nonnegative integers')
    if disk_free_bytes < remaining_output_bytes:
        raise ValueError('actual filesystem cannot cover this job remaining output')
    return {'status': 'ADMITTED_ACTUAL_CAPACITY', 'project_disk_limit_bytes': None,
            'project_ram_limit_bytes': None, 'project_vram_limit_bytes': None,
            'disk_free_bytes': disk_free_bytes, 'remaining_output_bytes': remaining_output_bytes,
            'shared_task_conflicts_must_be_checked': True}
