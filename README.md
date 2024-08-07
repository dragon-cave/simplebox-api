# Simplebox API

O refresh token tem expiração de 1 dia após a criação. O token de sessão tem expiração 5 minutos após a criação.

## Como executar 

Essas instruções são para executar o projeto localmente, caso queira executar em produção, consulte o repositório [simplebox](https://github.com/dragon-cave/simplebox).

### Linux

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations user simplebox
python manage.py migrate
python manage.py runserver
```

## Rotas

### Autenticação

#### Rota login - `/api/auth/login`
- **POST** - envia as credenciais de login, recebe de volta os tokens

#### Rota cadastro - `/api/auth/register`
- **POST** - envia os dados de cadastro, recebe de volta nada

#### Rota logout - `/api/auth/logout`
- **POST** - informa pro server que o usuário está fazendo logout (invalidar tokens)

#### Rota refresh - `/api/auth/refresh`
- **POST** - envia o refresh token, recebe um novo token de sessão

#### Rota mudança de senha - `/api/auth/change-password`
- **POST** - envia a senha antiga e a nova senha (com confirmação), atualiza a senha do usuário

### Informações do Usuário

#### Rota infos do usuário - `/api/user`
- **GET** - recebe as infos do usuário
- **PATCH** - atualiza as infos do usuário
