import os

import click
from click import ClickException

from . import workflow
from . import printer
from . import utils
from .runtime import runtime
from k8s_client import get_k8s_client, local_persistent_volume, create_secret, azure_persistent_volume


@click.group()
def main():
    pass


@main.command()
@click.option('-f', '--filename', help='Path for workflow.yaml file. ex) \'jupyterflow run -f workflow.yaml\'', default=None)
@click.option('-c', '--command', help="Command to run workflow. ex) \'jupyterflow run -c \"python main.py >> python next.py\"\'", default=None)
@click.option('-o', '--output', help='Output format. default is \'-o jsonpath="metadata.name"\'', default='jsonpath="metadata.name"')
@click.option('--dry-run', help='Only prints Argo Workflow object, without accually sending it', default=False, is_flag=True)
def run(filename, command, output, dry_run):

    if command is not None:
        user_workflow = workflow.load_from_command(command)
        workingDir = os.getcwd()
    elif filename is not None:
        if not os.path.isfile(filename):
            raise ClickException("No such file %s" % filename)
        user_workflow = workflow.load_from_file(filename)
        workingDir = os.path.dirname(os.path.abspath(filename))
    else:
        raise ClickException("Provide either `-f` or `-c` option")

    runtime['workingDir'] = workingDir
    namespace = runtime['namespace']
    conf = utils.load_config()
    wf, volumes_to_mount = workflow.build(user_workflow, namespace, runtime, conf)
    
    if dry_run:
        response = wf
        output = 'yaml'
    else:
        if (volumes_to_mount != None and len(volumes_to_mount) != 0):
            client = get_k8s_client('eyJhbGciOiJSUzI1NiIsImtpZCI6IlJmX3JacmVITmdTak5BaHNINWlONlE1cGNwam00cEgzX2FKNFIwWXQ4b2cifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJqaHViIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InZvbHVtZS1tYW5hZ2VyLXRva2VuLWpxaDZzIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6InZvbHVtZS1tYW5hZ2VyIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiZTRiZTAxM2MtODg0Ni00ODMxLTgyMzYtZjBiN2Q3YjEzMmIxIiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmpodWI6dm9sdW1lLW1hbmFnZXIifQ.2eQGsSa7mtOXtSOH6WiCCDwufMen08f0J_7WzVvqNBwvV2NOqZ89fX18Aal1L24ndCwXVw-GEYsoHlWQ_mwbZ-SydxBvMhJaGDtbvh40RhRyUeVYfBs37xyiUE8OU9XNdH9lDAKJOjmoavLLkonSuCvmThtnj_0wPQKdLhMHo-a3rHXiGYk_CFqoPoQY4n6kIste1N9fapGxGa0lhjke_SNLDxlK99WLnkDRh6vSNqWswoPjvuhstxEI6axkvHnQRe7qAiWEdxluZoEF6DLCZvUefq3WkKZShz5mOhvVHb1nzqRY9pV5BKJrWCPncYlLveKuIwDIrMgsETw7BxHK8g')
            # Mount the new volumes here
            print("Mounting Volumes here")
            for volume in volumes_to_mount:
                mount_options, volume_type = getVolumeDetails(volume)
                if (volume_type == 'azure'):
                    secret_name = mount_options['volume_name'] + '-secret'
                    create_secret(client, secret_name, mount_options['name'], mount_options['key'])
                    azure_persistent_volume(client, mount_options['volume_name'], mount_options['size'], secret_name, mount_options['fileshareName'], namespace)
                elif (volume_type == 'local'):
                    local_persistent_volume(client, mount_options['volume_name'], mount_options['size'], mount_options['path'], mount_options['hostname'], namespace);
                else:
                    raise ClickException("Failed to mount volumes")
        # response = workflow.run(wf, namespace)

    printer.format(response, output)

@main.command()
@click.argument('name')
def delete(name):
    response = workflow.delete(name, runtime['namespace'])
    printer.format(response, 'text')


@main.command()
@click.option('--generate-config', help='Generate config file', default=False, is_flag=True)
def config(generate_config):
    if generate_config:
        utils.create_config()
        printer.format('jupyterflow config file created', 'text')
    else:
        conf = utils.load_config()
        printer.format(conf, 'yaml')
