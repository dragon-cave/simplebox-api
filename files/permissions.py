from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from ipaddress import ip_address, ip_network

class IsPrivateSubnet(BasePermission):
    """
    Custom permission to only allow access from IPs within specified subnets.
    """
    subnet_cidrs = ['10.0.128.0/20', '10.0.144.0/20']

    def __init__(self):
        # Compile the subnet CIDRs into ip_network objects for efficient lookup
        self.subnets = [ip_network(subnet, strict=False) for subnet in self.subnet_cidrs]

    def get_client_ip(self, request):
        # Retrieve the IP address from X-Forwarded-For header or fall back to REMOTE_ADDR
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

    def has_permission(self, request, view):
        remote_ip = ip_address(self.get_client_ip(request))
        if not any(remote_ip in subnet for subnet in self.subnets):
            raise PermissionDenied("Access denied.")
        return True
