# import boto3
from cfn_flip import load_json, to_yaml, dump_yaml
from .helpers import resolve_element, get_filename_from_path, check_create_folder

def process_layer(cfn, key, value, target_asset_folder, layer_path, s3_client):
    print('Processing Layer: ' + key)
    source_bucket = resolve_element(
        cfn, value['Properties']['Content']['S3Bucket'])
    source_key = resolve_element(
        cfn, value['Properties']['Content']['S3Key'])
    target_path = f'{target_asset_folder}/{layer_path}/'
    check_create_folder(target_path)
    filename = get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, target_path + filename)
    value['Properties']['Content']['S3Bucket'] = {
        'Ref': 'AssetBucket'}
    value['Properties']['Content']['S3Key'] = {
        'Fn::Sub': target_path + source_key}

def process_statemachine(cfn, key, value, target_asset_folder, statemachine_path, s3_client):
    print('Processing Satemachine: ' + key)
    source_bucket = resolve_element(
        cfn, value['Properties']['DefinitionS3Location']['Bucket'])
    source_key = resolve_element(
        cfn, value['Properties']['DefinitionS3Location']['Key'])
    target_sub_path = f'{target_asset_folder}/{statemachine_path}/'
    filename = get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, target_asset_folder + target_sub_path + filename)
    value['Properties']['DefinitionS3Location']['Bucket'] = {
        'Ref': 'EEAssetsBucket'}
    value['Properties']['DefinitionS3Location']['Key'] = {
        'Fn::Sub': 'modules/${EEModuleId}/v${EEModuleVersion}/cfn' + target_sub_path + source_key}

def process_template(cfn_input_template, cfn_output_template, target_asset_folder, layer_path, statemachine_path, s3_client):
    with open(cfn_input_template) as f:
        str_cfn = f.read()

        cfn = load_json(str_cfn)
        resources = cfn["Resources"]

        for key, value in resources.items():
            # if value["Type"] == "AWS::Lambda::Function":
            #     print(f'Processing: {key}')
            #     if 'S3Bucket' in value['Properties']['Code']:
            #         source_bucket = resolve_element(
            #             cfn, value['Properties']['Code']['S3Bucket'])
            #         source_key = resolve_element(
            #             cfn, value['Properties']['Code']['S3Key'])
            #         target_sub_path = '/lambda/'
            #         filename = get_filename_from_path(source_key)
            #         handler = value['Properties']['Handler']
            #         s3_client.download_file(
            #             source_bucket, source_key, TARGET_ASSET_FOLDER + target_sub_path + filename)
            #         if 'InlineSAMFunction' in value["Metadata"] and value["Metadata"]['InlineSAMFunction'] == True:
            #             print(f'going to inine {key}')
            #             lambda_source = get_lambda_source(
            #                 TARGET_ASSET_FOLDER + target_sub_path + filename, handler)
            #             value['Properties']['Code']['ZipFile'] = lambda_source
            #             del value['Properties']['Code']['S3Bucket']
            #             del value['Properties']['Code']['S3Key']
            #         else:
            #             value['Properties']['Code']['S3Bucket'] = {
            #                 'Ref': 'EEAssetsBucket'}
            #             value['Properties']['Code']['S3Key'] = {
            #                 'Fn::Sub': 'modules/${EEModuleId}/v${EEModuleVersion}/cfn' + target_sub_path + source_key}
            #     else:
            #         print(f'Code is not referenced from an S3 Bucket')
            if value["Type"] == "AWS::Lambda::LayerVersion":
                process_layer(cfn, key, value, target_asset_folder, layer_path, s3_client)
            elif value["Type"] == "AWS::StepFunctions::StateMachine":
                process_statemachine(cfn, key, value, target_asset_folder, statemachine_path, s3_client)
    with open(cfn_output_template, 'w') as f:
        f.write(to_yaml(dump_yaml(cfn), clean_up=True))