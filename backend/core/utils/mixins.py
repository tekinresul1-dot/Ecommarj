# backend/core/utils/mixins.py

from rest_framework import permissions

class TenantQuerySetMixin:
    """
    Automatically filters querysets so that users only see data belonging to their Organization.
    Assumes the model has an `organization` ForeignKey.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # If user is not authenticated, they get nothing
        if not user.is_authenticated:
            return qs.none()
            
        # If user has no profile/organization, they get nothing
        if not hasattr(user, 'profile') or not user.profile.organization:
            return qs.none()
            
        return qs.filter(organization=user.profile.organization)

    def perform_create(self, serializer):
        """Automatically set the organization on create."""
        serializer.save(organization=self.request.user.profile.organization)
