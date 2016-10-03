API
===

krbcontext.context
------------------

.. autoclass:: krbcontext.context.krbContext
   :members:
   :special-members:

.. autoexception:: krbcontext.context.KRB5InitError

.. autofunction:: krbcontext.context.init_ccache_as_regular_user

.. autofunction:: krbcontext.context.init_ccache_with_keytab

.. autofunction:: krbcontext.context.get_default_ccache

.. autofunction:: krbcontext.context.is_initialize_ccache_necessary

.. autofunction:: krbcontext.context.clean_context_options

.. autofunction:: krbcontext.context.init_ccache_if_necessary

krbcontext.utils
----------------

.. autoclass:: krbcontext.utils.CredentialTime
   :special-members: 

.. autofunction:: krbcontext.utils.get_login

.. autofunction:: krbcontext.utils.build_tgt_ticket

.. autofunction:: krbcontext.utils.get_tgt_time
