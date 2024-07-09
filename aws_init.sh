#!/bin/bash

# Variáveis
INSTANCE_NAME="Dragoncave"
INSTANCE_TYPE="t2.micro"
AMI_ID="ami-04b70fa74e45c3917" # Substitua pelo ID do AMI que você deseja usar
KEY_NAME="our-key"
SECURITY_GROUP_NAME="proof-security-group"
KEY_FILE="${KEY_NAME}.pem"

# Script de usuário para ser executado na inicialização da instância EC2
USER_DATA=$(cat <<EOF
#!/bin/bash
# Comandos para serem executados na inicialização

# comandos de instalação e inicialização dos servidores

# backend

#sudo apt install python3 python3-venv

# git clone -b v1.0 https://github.com/dragon-cave/simplebox-api
# cd simplebox-api

# python -m venv venv
# source venv/bin/activate
# pip install django djangorestframework cors-headers
# python manage.py migrate
# python manage.py makemigrations
# nohup python manage.py runserver 0.0.0.0:8000 &

EOF
)

# Criar um par de chaves
aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > $KEY_FILE

# Configurar permissões para o arquivo de chave
# chmod 400 $KEY_FILE

# Criar um grupo de segurança
SECURITY_GROUP_ID=$(aws ec2 create-security-group --group-name $SECURITY_GROUP_NAME --description "Security group with open inbound traffic" --query 'GroupId' --output text)

# Adicionar uma regra para permitir todo o tráfego de entrada
aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol -1 --port -1 --cidr 0.0.0.0/0

# Executar uma instância EC2 com UserData
INSTANCE_ID=$(aws ec2 run-instances --image-id $AMI_ID --count 1 --instance-type $INSTANCE_TYPE --key-name $KEY_NAME --security-group-ids $SECURITY_GROUP_ID --user-data "$USER_DATA" --query 'Instances[0].InstanceId' --output text)

# Adicionar uma tag para nomear a instância
aws ec2 create-tags --resources $INSTANCE_ID --tags Key=Name,Value=$INSTANCE_NAME

# Obter o endereço IP público da instância
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

# Exibir o ID da instância e o endereço IP público
echo "EC2 instance started with ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Key pair created: $KEY_FILE (stored in the current directory)"

# Conectar-se à instância via SSH (opcional)
echo "To connect to the instance via SSH, use the following command:"
echo "ssh -i $KEY_FILE ubuntu@$PUBLIC_IP"