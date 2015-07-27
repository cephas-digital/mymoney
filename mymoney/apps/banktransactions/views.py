from collections import OrderedDict

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage, Paginator
from django.core.urlresolvers import reverse
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views import generic

from .forms import (
    BankTransactionCreateForm, BankTransactionListForm,
    BankTransactionUpdateForm
)
from .mixins import BankTransactionAccessMixin, BankTransactionSaveViewMixin
from .models import BankTransaction


class BankTransactionListView(BankTransactionAccessMixin, generic.FormView):

    form_class = BankTransactionListForm
    template_name = 'banktransactions/list/index.html'
    paginate_by = 50
    _session_key = 'banktransactionlistform'

    def get_initial(self):
        initial = super(BankTransactionListView, self).get_initial()

        if self._session_key in self.request.session:
            session = self.request.session
            initial.update(session[self._session_key].get('filters', {}))
            initial.update(session[self._session_key].get('raw_input', {}))

        return initial

    def get_form_kwargs(self):
        kwargs = super(BankTransactionListView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['bt_ids'] = [bt.pk for bt in self.page]

        submits = set(('filter', 'reset', 'action')) & set(self.request.POST.keys())
        kwargs['submit'] = submits.pop() if submits else None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BankTransactionListView, self).get_context_data(**kwargs)

        context['bankaccount'] = self.bankaccount
        context['has_filters'] = self._session_key in self.request.session
        context['current_balance'] = (
            BankTransaction.objects.get_current_balance(self.bankaccount)
        )
        context['reconciled_balance'] = (
            BankTransaction.objects.get_reconciled_balance(self.bankaccount)
        )

        context['object_list'] = self.page.object_list
        context['page_obj'] = self.page
        context['is_paginated'] = self.page.has_other_pages()

        return context

    def get_success_url(self):
        self.success_url = reverse('banktransactions:list', kwargs={
            'bankaccount_pk': self.bankaccount.pk,
        })
        return super(BankTransactionListView, self).get_success_url()

    def form_valid(self, form):

        if 'filter' in self.request.POST:
            filters, raw_input = {}, {}
            for key, value in form.cleaned_data.items():
                value = list(value) if isinstance(value, QuerySet) else value

                if (key.startswith('banktransaction_') or key == 'operation'
                        or value in form.fields[key].empty_values):
                    continue

                if key == 'tags':
                    data = [tag.pk for tag in value]
                elif key.startswith('date_') or key.startswith('amount_'):
                    raw_input[key] = self.request.POST.get(key, None)
                    data = str(value)
                else:
                    data = value

                filters[key] = data

            self.request.session[self._session_key] = {
                'filters': filters,
                'raw_input': raw_input,
            }

        elif 'reset' in self.request.POST:
            if self._session_key in self.request.session:
                del self.request.session[self._session_key]

        elif 'action' in self.request.POST:  # pragma: no branch
            op = form.cleaned_data['operation']
            ids = form.cleaned_data['banktransactions']

            if op == 'reconcile':
                (BankTransaction.objects
                    .filter(pk__in=ids)
                    .update(reconciled=True))
                messages.success(
                    self.request,
                    _('Bank transaction have been reconciled.'),
                )

            elif op == 'unreconcile':
                (BankTransaction.objects
                    .filter(pk__in=ids)
                    .update(reconciled=False))
                messages.success(
                    self.request,
                    _('Undo bank transaction reconciled.'),
                )

            elif op == 'delete':  # pragma: no branch
                self.request.session['banktransactionlistdelete'] = list(ids)
                return HttpResponseRedirect(reverse(
                    'banktransactions:delete_multiple', kwargs={
                        'bankaccount_pk': self.bankaccount.pk
                    }
                ))

        return super(BankTransactionListView, self).form_valid(form)

    @cached_property
    def page(self):

        paginator = Paginator(self.queryset, self.paginate_by)
        try:
            page = paginator.page(self.request.GET.get('page'))
        except InvalidPage:
            page = paginator.page(1)

        return page

    @property
    def queryset(self):

        qs = (
            BankTransaction.objects
            .filter(bankaccount=self.bankaccount)
            .select_related('tag')
            .order_by('-date', '-id')
        )

        # Unfortunetly, we cannot get it by doing the opposite (i.e :
        # total balance - SUM(futur bt) because with postgreSQL at least,
        # the last dated bt would give None : total balance - SUM(NULL)
        total_balance_subquery = """
            SELECT SUM(bt_sub.amount)
            FROM {table} AS bt_sub
            WHERE
                bt_sub.bankaccount_id = %s
                AND (
                    bt_sub.date < {table}.date
                    OR (
                        bt_sub.date = {table}.date
                        AND
                        bt_sub.id <= {table}.id
                    )
                )
            """.format(table=BankTransaction._meta.db_table)

        reconciled_balance_subquery = """
            SELECT SUM(bt_sub_r.amount)
            FROM {table} AS bt_sub_r
            WHERE
                bt_sub_r.bankaccount_id = %s
                AND
                bt_sub_r.reconciled = \'1\'
                AND (
                    bt_sub_r.date < {table}.date
                    OR (
                        bt_sub_r.date = {table}.date
                        AND
                        bt_sub_r.id <= {table}.id
                    )
                )""".format(table=BankTransaction._meta.db_table)

        qs = qs.extra(
            select=OrderedDict([
                ('total_balance', total_balance_subquery),
                ('reconciled_balance', reconciled_balance_subquery),
            ]),
            select_params=(self.bankaccount.pk, self.bankaccount.pk)
        )

        if self._session_key in self.request.session:
            filters = self.request.session[self._session_key].get('filters', {})

            if 'label' in filters:
                qs = qs.filter(label__icontains=filters['label'])

            if 'date_start' in filters and 'date_end' in filters:
                qs = qs.filter(date__range=(
                    filters['date_start'],
                    filters['date_end'])
                )
            elif 'date_start' in filters:
                qs = qs.filter(date__gte=filters['date_start'])
            elif 'date_end' in filters:
                qs = qs.filter(date__lte=filters['date_end'])

            if 'amount_min' in filters and 'amount_max' in filters:
                qs = qs.filter(amount__range=(
                    filters['amount_min'],
                    filters['amount_max'])
                )
            elif 'amount_min' in filters:
                qs = qs.filter(amount__gte=filters['amount_min'])
            elif 'amount_max' in filters:
                qs = qs.filter(amount__lte=filters['amount_max'])

            if 'status' in filters:
                qs = qs.filter(status=filters['status'])

            if 'reconciled' in filters:
                qs = qs.filter(reconciled=filters['reconciled'])

            if 'tags' in filters:
                qs = qs.filter(tag__in=filters['tags'])

        return qs


class BankTransactionCreateView(BankTransactionAccessMixin,
                                BankTransactionSaveViewMixin,
                                SuccessMessageMixin,
                                generic.CreateView):

    form_class = BankTransactionCreateForm
    success_message = ugettext_lazy(
        "Bank transaction %(label)s was created successfully."
    )
    permissions = ('banktransactions.add_banktransaction',)

    def get_initial(self):

        initial = super(BankTransactionCreateView, self).get_initial()
        if self.request.GET.get('self-redirect', False):
            initial['redirect'] = True
        return initial

    def form_valid(self, form):

        response = super(BankTransactionCreateView, self).form_valid(form)
        if form.cleaned_data['redirect']:

            url_redirect = reverse('banktransactions:create', kwargs={
                'bankaccount_pk': self.object.bankaccount.pk,
            }) + '?self-redirect=1'
            return HttpResponseRedirect(url_redirect)

        return response


class BankTransactionUpdateView(BankTransactionAccessMixin,
                                BankTransactionSaveViewMixin,
                                SuccessMessageMixin,
                                generic.UpdateView):

    form_class = BankTransactionUpdateForm
    success_message = ugettext_lazy(
        "Bank transaction %(label)s was updated successfully."
    )
    permissions = ('banktransactions.change_banktransaction',)


class BankTransactionDeleteView(BankTransactionAccessMixin,
                                generic.DeleteView):

    model = BankTransaction
    permissions = ('banktransactions.delete_banktransaction',)

    def get_success_url(self):
        """
        Override parent to dynamically set success url.
        """
        self.success_url = reverse('banktransactions:list', kwargs={
            'bankaccount_pk': self.object.bankaccount.pk,
        })
        return super(BankTransactionDeleteView, self).get_success_url()


class BankTransactionDeleteMultipleView(BankTransactionAccessMixin,
                                        generic.TemplateView):

    template_name = 'banktransactions/banktransaction_confirm_delete_multiple.html'
    permissions = ('banktransactions.delete_banktransaction',)
    banktransactions = None

    def dispatch(self, request, *args, **kwargs):

        if 'banktransactionlistdelete' in self.request.session:
            self.banktransactions = BankTransaction.objects.filter(
                pk__in=self.request.session['banktransactionlistdelete']
            )

        if not self.banktransactions:
            raise PermissionDenied

        return super(BankTransactionDeleteMultipleView, self).dispatch(
            request, *args, **kwargs
        )

    def post(self, request, *args, **kwargs):

        for banktransaction in self.banktransactions:
            banktransaction.delete()

        del self.request.session['banktransactionlistdelete']
        messages.success(request, "Bank transactions deleted successfully.")

        return HttpResponseRedirect(reverse('banktransactions:list', kwargs={
            'bankaccount_pk': self.bankaccount.pk,
        }))

    def get_context_data(self, **kwargs):
        context = super(BankTransactionDeleteMultipleView, self).get_context_data(**kwargs)
        context['bankaccount'] = self.bankaccount
        context['banktransactions'] = self.banktransactions
        return context