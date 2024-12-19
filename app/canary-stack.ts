
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as synthetics from 'aws-cdk-lib/aws-synthetics';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as cloudwatch_actions from 'aws-cdk-lib/aws-cloudwatch-actions';

export class CanaryStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Define an SNS topic for canary alarm notifications
    const alertTopic = new sns.Topic(this, 'CanaryAlertTopic');

    // Create a new canary
    const canary = new synthetics.Canary(this, 'NewCanary', {
      runtime: synthetics.Runtime.SYNTHETICS_NODEJS_PUPPETEER_3_3,
      test: synthetics.Test.custom({
        code: synthetics.Code.fromInline(`
          var synthetics = require('Synthetics');
          const log = require('SyntheticsLogger');

          exports.handler = async function () {
            // Insert your canary script here
            await synthetics.executeHttpStep('Verify site', async function () {
              return await synthetics.executeHttpStep('Verify site', async function (request) {
                request.url = "https://example.com";
                request.method = "GET";
                request.headers = {"User-Agent": "Synthetics"};
              });
            });
          };
        `),
      }),
      schedule: synthetics.Schedule.rate(cdk.Duration.minutes(5)),
    });

    // Create a CloudWatch alarm for the canary
    const canaryAlarm = new cloudwatch.Alarm(this, 'CanaryFailureAlarm', {
      metric: canary.metricFailed(),
      threshold: 1,
      evaluationPeriods: 1,
    });

    // Attach actions to the alarm
    canaryAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alertTopic));
    canaryAlarm.addOkAction(new cloudwatch_actions.SnsAction(alertTopic));
  }
}
