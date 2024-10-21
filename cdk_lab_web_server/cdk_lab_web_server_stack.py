import os.path

from aws_cdk.aws_s3_assets import Asset as S3asset

from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds
    # aws_sqs as sqs,
)

from constructs import Construct

dirname = os.path.dirname(__file__)
        
class CdkLabWebServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cdk_lab_vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Instance Role and SSM Managed Policy
        InstanceRole = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        InstanceRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        
        # Security Group for Web Servers
        web_sg = ec2.SecurityGroup(self, "WebServerSG", vpc=cdk_lab_vpc, description="Allow HTTP traffic to web servers")
        web_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP from anywhere")

        # Create EC2 instances in public subnets
        for i, subnet in enumerate(cdk_lab_vpc.public_subnets):
            ec2.Instance(self, f"WebServer{i + 1}", 
                         vpc=cdk_lab_vpc,
                         instance_type=ec2.InstanceType("t2.micro"),
                         machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                         role=InstanceRole,
                         security_group=web_sg)

        # Security Group for RDS
        rds_sg = ec2.SecurityGroup(self, "RDSSG", vpc=cdk_lab_vpc, description="Allow MySQL traffic from web servers")
        rds_sg.add_ingress_rule(web_sg, ec2.Port.tcp(3306), "Allow MySQL from web servers")

        # Create RDS Instance
        rds_instance = rds.DatabaseInstance(self, "MyRDS",
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0),
            instance_type=ec2.InstanceType("t2.micro"),
            vpc=cdk_lab_vpc,
            vpc_subnets={"subnet_type": ec2.SubnetType.PRIVATE_WITH_NAT},
            security_groups=[rds_sg],
            multi_az=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            deletion_protection=False,
            database_name="MyDatabase"
        )

        """  # Create an EC2 instance
        cdk_lab_web_instance = ec2.Instance(self, "cdk_lab_web_instance", vpc=cdk_lab_vpc,
                                            instance_type=ec2.InstanceType("t2.micro"),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            role=InstanceRole)


        # Script in S3 as Asset
        webinitscriptasset = S3asset(self, "Asset", path=os.path.join(dirname, "configure.sh"))
        asset_path = cdk_lab_web_instance.user_data.add_s3_download_command(
            bucket=webinitscriptasset.bucket,
            bucket_key=webinitscriptasset.s3_object_key
        )

        # Userdata executes script from S3
        cdk_lab_web_instance.user_data.add_execute_file_command(
            file_path=asset_path
            )
        webinitscriptasset.grant_read(cdk_lab_web_instance.role)
        
        # Allow inbound HTTP traffic in security groups
        cdk_lab_web_instance.connections.allow_from_any_ipv4(ec2.Port.tcp(80)) """
