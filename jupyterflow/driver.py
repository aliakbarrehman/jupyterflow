import os

# import click
# from click import ClickException

import workflow
import printer
import utils
from runtime import runtime


# @click.group()
# def main():
#     pass


# @main.command()
# @click.option('-f', '--filename', help='Path for workflow.yaml file. ex) \'jupyterflow run -f workflow.yaml\'', default=None)
# @click.option('-c', '--command', help="Command to run workflow. ex) \'jupyterflow run -c \"python main.py >> python next.py\"\'", default=None)
# @click.option('-o', '--output', help='Output format. default is \'-o jsonpath="metadata.name"\'', default='jsonpath="metadata.name"')
# @click.option('--dry-run', help='Only prints Argo Workflow object, without accually sending it', default=False, is_flag=True)
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
    wf, volumesToMount = workflow.build(user_workflow, namespace, runtime, conf)
    
    if (volumesToMount != None and len(volumesToMount) != 0):
        # Mount the new volumes here
        print("Mounting Volumes here")
        # 1. Write a function that takes volumesToMount as input and mounts them one by one
        #   a. Read env variables (at the moment) for values like azure file share name or key (for local read path)
        # 2. If Failed to mount throw error
        # 3. If mount successfull proceed
    
    if dry_run:
        response = wf
        output = 'yaml'
    else:
        response = workflow.run(wf, namespace)

    printer.format(response, output)


# @main.command()
# @click.argument('name')
def delete(name):
    response = workflow.delete(name, runtime['namespace'])
    printer.format(response, 'text')


# @main.command()
# @click.option('--generate-config', help='Generate config file', default=False, is_flag=True)
def config(generate_config):
    if generate_config:
        utils.create_config()
        printer.format('jupyterflow config file created', 'text')
    else:
        conf = utils.load_config()
        printer.format(conf, 'yaml')
