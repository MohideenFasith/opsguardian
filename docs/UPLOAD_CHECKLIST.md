# Devpost upload checklist

## Repository

- [ ] Create a **public** GitHub/GitLab/Bitbucket repository.
- [ ] Upload the contents of this ZIP, not the ZIP as a single opaque file.
- [ ] Confirm `README.md` renders the architecture image.
- [ ] Confirm `LICENSE` is visible and the repository reports MIT licensing.
- [ ] Confirm there is no `.env`, AWS key, secret, account ID, private dataset, or local database in Git history.
- [ ] Run GitHub CI or `pytest -q` after upload.

## AWS

- [ ] Create/confirm AWS account and AWS Builder ID.
- [ ] Request hackathon AWS promotional credits if still available.
- [ ] Enable access to the Bedrock model used for the live demo.
- [ ] Run `./scripts/deploy_agentcore.sh` if you want the AgentCore technical-score boost.
- [ ] Save real AgentCore status/log/console evidence for the demo video.

## Demo video — maximum five minutes

- [ ] Show the problem, intended user, and why it matters.
- [ ] Show the working product end to end.
- [ ] Show genuine Strands/AgentCore evidence, not generated mock footage.
- [ ] Upload publicly to YouTube or Vimeo.
- [ ] Paste the public video URL into Devpost.

## Devpost

- [ ] Select **Professional Agents**.
- [ ] Paste/adapt `docs/DEVPOST_SUBMISSION.md`.
- [ ] Add the public repository URL.
- [ ] Add AWS Builder ID.
- [ ] Add architecture diagram.
- [ ] Add public video URL.
- [ ] Add optional live demo URL if you deploy the web UI.

## Bonus

- [ ] Publish the builder.aws.com article using `docs/BONUS_BUILDER_POST.md` as a draft.
- [ ] Follow the hackathon's current required title/tag wording when publishing.
