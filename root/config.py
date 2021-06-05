# Secret_key: Using for session.
secret_key = "secret-key"  # Change to any string you like.

# Server settings
server_title = "异想之旅"  # Your group or company name.
index_title = "异想之旅轻量网盘服务"  # Your server's name, shows on index title.

# Running settings.
listening_port = "8000"
listening_host = "127.0.0.1"
debug_mode = True

# Warning: debug_key is created for test the program, for the server's safety,
# please don't keep it empty. Write down anything you like if you don't need it!
debug_key = "debug-key"

# Redis
redis_host = "redis.server.host"
redis_port = 6379
redis_password = "password"  # Keep an empty string here if your server don't need a password.

# Check text
check_text = False
# Make sure you have the function to check text before you write down true.

# Relative path of file saving dir
save_path = "files"

# Admin username
admin_username = ["异想之旅"]

# Usernames that should be refused
# 1. Some public names: Usernames start with these words can login without checking the password, so they can't be signed.
refuse_startswith = ["test", "temp"]
# 2. Refuse the names that includes these words(usually put your server name in it).
refuse_including = ["异想之旅", "yxzl", "yixiangzhilv"]

# Limiter
default_limits = ["15 per 2 second"]

# Email config
check_email_before_sign_up = True
coder_email_address = "coder@yixiangzhilv.com"
coder_email_password = "password"
contact_email = "mail@yixiangzhilv.com"

