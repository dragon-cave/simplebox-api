from rest_framework.permissions import BasePermission
from ipaddress import ip_address, ip_network

class IsPrivateSubnet(BasePermission):
    """
    Custom permission to only allow access from IPs within a private subnet.
    """
    
    def __init__(self, subnet):
        self.subnet = ip_network(subnet, strict=False)
    
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
