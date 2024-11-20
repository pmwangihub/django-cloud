from typing import Any, Dict, Optional
from django.http import HttpRequest
from django.utils.http import url_has_allowed_host_and_scheme


class RequestFormAttachMixin:
    """
    Mixin to attach the request object to the form kwargs.
    """

    def get_form_kwargs(self) -> Dict[str, Any]:
        """
        Returns the form keyword arguments with the request object attached.

        :return: A dictionary containing form keyword arguments.
        """
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class NextUrlMixin:
    """
    Mixin to handle redirection to a 'next' URL if it's valid,
    or fallback to a default URL.
    """

    default_next: str = "/"

    def get_next_url(self) -> str:
        """
        Returns the next URL for redirection, ensuring that it is safe (i.e.,
        belongs to the same host or is a permitted URL). If not, returns the
        default URL.

        :return: A string representing the next URL to redirect to.
        """
        request: HttpRequest = self.request
        next_: Optional[str] = request.GET.get("next")
        next_post: Optional[str] = request.POST.get("next")
        redirect_path: Optional[str] = next_ or next_post or None

        if redirect_path and url_has_allowed_host_and_scheme(
            redirect_path, allowed_hosts={request.get_host()}
        ):
            return redirect_path

        return self.default_next
