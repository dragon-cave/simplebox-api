# DO NOT RUN THIS FILE!
# Run the setup file in simplebox repo instead

cd /home/ubuntu/simplebox/simplebox-api
source venv/bin/activate
gunicorn -b 0.0.0.0:8001 simplebox.wsgi