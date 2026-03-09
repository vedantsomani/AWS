"""AWS Bedrock model registry for Build & Host.

NOTE: Newer Anthropic models require cross-region inference profile IDs
(prefixed with 'us.') rather than direct model IDs.
See: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html
"""

# Amazon-native models work without AWS Marketplace subscription.
# Claude models require: AWS Console → Bedrock → Model access → Request access
# AND a valid payment instrument on the AWS account.
BEDROCK_MODELS = [
    {
        "key": "amazon-nova-pro",
        "model_id": "us.amazon.nova-pro-v1:0",
        "name": "Amazon Nova Pro",
        "provider": "Amazon",
        "tier": "flagship",
        "color": "orange",
        "description": "Amazon's most capable model. No marketplace subscription needed.",
        "max_tokens": 5120,
    },
    {
        "key": "amazon-nova-lite",
        "model_id": "us.amazon.nova-lite-v1:0",
        "name": "Amazon Nova Lite",
        "provider": "Amazon",
        "tier": "standard",
        "color": "emerald",
        "description": "Fast & cost-efficient. No marketplace subscription needed.",
        "max_tokens": 5120,
    },
    {
        "key": "amazon-nova-micro",
        "model_id": "us.amazon.nova-micro-v1:0",
        "name": "Amazon Nova Micro",
        "provider": "Amazon",
        "tier": "budget",
        "color": "teal",
        "description": "Fastest & cheapest. No marketplace subscription needed.",
        "max_tokens": 5120,
    },
    {
        "key": "claude-3-7-sonnet",
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "tier": "premium",
        "color": "violet",
        "description": "Requires AWS Marketplace subscription + payment method.",
        "max_tokens": 8000,
    },
    {
        "key": "claude-3-5-sonnet-v2",
        "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "name": "Claude 3.5 Sonnet v2",
        "provider": "Anthropic",
        "tier": "premium",
        "color": "blue",
        "description": "Requires AWS Marketplace subscription + payment method.",
        "max_tokens": 8000,
    },
    {
        "key": "claude-3-5-haiku",
        "model_id": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "tier": "standard",
        "color": "cyan",
        "description": "Requires AWS Marketplace subscription + payment method.",
        "max_tokens": 8000,
    },
]

MODELS_BY_KEY = {m["key"]: m for m in BEDROCK_MODELS}
DEFAULT_MODEL = "amazon-nova-pro"
