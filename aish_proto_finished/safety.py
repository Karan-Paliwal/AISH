DANGEROUS = ["rm -rf /", "mkfs", ":(){:|:&};:"]

def is_safe(cmd):
    return not any(danger in cmd for danger in DANGEROUS)
