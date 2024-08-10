### Triggers

These will be run when certaine events occur on github, such as a push to a certain branch. They can also be activated manually from the cloud build page, via triggers.

Triggers are created per branch, so a different env file can be used by the trigger.

The Trigger can also be given variable substitutions to apply, applying these when reading the `cloudbuild.yaml` file that tells it the steps it needs to perform.

So to control veriables at the code level, use different environment files. This file is then a substitution variable that the build will fetch when the trigger is triggered.

To control other variables, required during the building and deployment steps, use variable substitutions when creating the trigger.