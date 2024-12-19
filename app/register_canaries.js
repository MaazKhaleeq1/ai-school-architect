
const synthetics = require('synthetics');
const path = require('path');

const healthCheckCanary = new synthetics.Canary(this, 'HealthCheckCanary', {
  code: synthetics.Code.fromAsset(path.join(__dirname, '../../canaries/canary_health_check.js')),
  runtime: synthetics.Runtime.SYNTHETICS_NODEJS_PUPPETEER_3_2,
  schedule: synthetics.Schedule.rate(cdk.Duration.minutes(5)),
});

const loadTestCanary = new synthetics.Canary(this, 'LoadTestCanary', {
  code: synthetics.Code.fromAsset(path.join(__dirname, '../../canaries/canary_load_test.js')),
  runtime: synthetics.Runtime.SYNTHETICS_NODEJS_PUPPETEER_3_2,
  schedule: synthetics.Schedule.rate(cdk.Duration.minutes(10)),
});
