from rest_framework.permissions import BasePermission
from ipaddress import ip_address, ip_network

class IsPrivateSubnet(BasePermission):
    """
    Custom permission to only allow access from IPs within specified subnets.
    """
    subnet_cidrs = [ '10.0.128.0/20', '10.0.144.0/20' ]
    
    def __init__(self):
        self.subnets = [ip_network(subnet, strict=False) for subnet in self.subnet_cidrs]
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

    def has_permission(self, request, view):
        remote_ip = ip_address(self.get_client_ip(request))
        return any(remote_ip in subnet for subnet in self.subnets)