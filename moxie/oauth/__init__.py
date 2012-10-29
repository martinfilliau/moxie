from .views import Authorized, Authorize, VerifyCallback


def attach_oauth(blueprint, prefix='/oauth',
        authorized_route='/authorized',
        authorize_route='/authorize',
        verify_route='/verify'):
    # URL Rules
    blueprint.add_url_rule(prefix + authorized_route,
            view_func=Authorized.as_view('authorized'))

    blueprint.add_url_rule(prefix + authorize_route,
            view_func=Authorize.as_view('authorize'))

    blueprint.add_url_rule(prefix + verify_route,
            view_func=VerifyCallback.as_view('verify'))

    return blueprint
