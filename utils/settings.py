def init(args):

	global iam_role_list
	global lambda_function_list
	global region
	global environment
	global DATA_POLICY

	# iam_role_eks_worker and iam_role_efs_provisioner are special case
	# so deal with them separately
	iam_role_list = [
		"iam_role_lambda_common",
		"iam_role_codebuild",
		"iam_role_codepipeline",
		"iam_role_eks_cluster",
		"iam_role_rds_monitoring",
	]


	lambda_function_list = [
		"lambda_product_image_copy",
		"lambda_nextail_transfer",
		"lambda_nextail_transfer_s3_ownership",
		"lambda_storemaster_datalake",
		"lambda_storemaster",
		"lambda_sns_to_slack_alerts",
		"lambda_price_product_backbone",
		"lambda_price_monitor_nextail"
	]

	region = args.region
	environment = args.environment

	# place holders
	DATA_POLICY = {
		"Version": "2012-10-17",
		"Statement": [
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
			{
				"Effect": "Allow",
				"Action": "ACTION_ALLOW",
				"Resource": "RESOURCE_ALLOW",
			},
		]
	}
