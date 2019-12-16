# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import graphene
import json

from django.conf import settings
from django.core.paginator import Paginator

from django_mysql.models import JSONField

from graphene.types.generic import GenericScalar

from graphene_django.converter import convert_django_field
from graphene_django.types import DjangoObjectType

from .api import (add_identity,
                  delete_identity,
                  update_profile,
                  move_identity,
                  merge_identities,
                  add_organization,
                  add_domain,
                  delete_organization,
                  delete_domain,
                  enroll,
                  withdraw)
from .models import (Organization,
                     Domain,
                     Country,
                     UniqueIdentity,
                     Identity,
                     Profile,
                     Enrollment,
                     Transaction,
                     Operation)


@convert_django_field.register(JSONField)
def convert_json_field_to_generic_scalar(field, registry=None):
    """Convert the content of a `JSONField` loading it as an object"""

    return OperationArgsType(description=field.help_text, required=not field.null)


class PaginationType(graphene.ObjectType):
    page = graphene.Int()
    page_size = graphene.Int()
    num_pages = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()
    start_index = graphene.Int()
    end_index = graphene.Int()
    total_results = graphene.Int()


class OperationArgsType(GenericScalar):
    @classmethod
    def serialize(cls, value):
        value = super().serialize(value)
        value = json.loads(value)
        return value


class OperationType(DjangoObjectType):
    class Meta:
        model = Operation


class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Organization


class DomainType(DjangoObjectType):
    class Meta:
        model = Domain


class CountryType(DjangoObjectType):
    class Meta:
        model = Country


class UniqueIdentityType(DjangoObjectType):
    class Meta:
        model = UniqueIdentity


class IdentityType(DjangoObjectType):
    class Meta:
        model = Identity


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class EnrollmentType(DjangoObjectType):
    class Meta:
        model = Enrollment


class ProfileInputType(graphene.InputObjectType):
    name = graphene.String(required=False)
    email = graphene.String(required=False)
    gender = graphene.String(required=False)
    gender_acc = graphene.Int(required=False)
    is_bot = graphene.Boolean(required=False)
    country_code = graphene.String(required=False)


class OrganizationFilterType(graphene.InputObjectType):
    name = graphene.String(required=False)


class IdentityFilterType(graphene.InputObjectType):
    uuid = graphene.String(required=False)


class TransactionFilterType(graphene.InputObjectType):
    tuid = graphene.String(required=False)
    name = graphene.String(required=False)
    is_closed = graphene.Boolean(required=False)
    from_date = graphene.DateTime(required=False)
    to_date = graphene.DateTime(required=False)


class OperationFilterType(graphene.InputObjectType):
    ouid = graphene.String(required=False)
    op_type = graphene.String(required=False)
    entity_type = graphene.String(required=False)
    target = graphene.String(required=False)
    from_date = graphene.DateTime(required=False)
    to_date = graphene.DateTime(required=False)


class AbstractPaginatedType(graphene.ObjectType):

    @classmethod
    def create_paginated_result(cls, query, page=1,
                                page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE):
        paginator = Paginator(query, page_size)
        result = paginator.page(page)

        entities = result.object_list

        page_info = PaginationType(
            page=result.number,
            page_size=page_size,
            num_pages=paginator.num_pages,
            has_next=result.has_next(),
            has_prev=result.has_previous(),
            start_index=result.start_index(),
            end_index=result.end_index(),
            total_results=len(query)
        )

        return cls(entities=entities, page_info=page_info)


class OrganizationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(OrganizationType)
    page_info = graphene.Field(PaginationType)


class IdentityPaginatedType(AbstractPaginatedType):
    entities = graphene.List(UniqueIdentityType)
    page_info = graphene.Field(PaginationType)


class TransactionPaginatedType(AbstractPaginatedType):
    entities = graphene.List(TransactionType)
    page_info = graphene.Field(PaginationType)


class OperationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(OperationType)
    page_info = graphene.Field(PaginationType)


class AddOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    organization = graphene.Field(lambda: OrganizationType)

    def mutate(self, info, name):
        org = add_organization(name)

        return AddOrganization(
            organization=org
        )


class DeleteOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    organization = graphene.Field(lambda: OrganizationType)

    def mutate(self, info, name):
        org = delete_organization(name)

        return DeleteOrganization(
            organization=org
        )


class AddDomain(graphene.Mutation):
    class Arguments:
        organization = graphene.String()
        domain = graphene.String()
        is_top_domain = graphene.Boolean()

    domain = graphene.Field(lambda: DomainType)

    def mutate(self, info, organization, domain, is_top_domain=False):
        dom = add_domain(organization, domain, is_top_domain=is_top_domain)

        return AddDomain(
            domain=dom
        )


class DeleteDomain(graphene.Mutation):
    class Arguments:
        domain = graphene.String()

    domain = graphene.Field(lambda: DomainType)

    def mutate(self, info, domain):
        dom = delete_domain(domain)

        return DeleteDomain(
            domain=dom
        )


class AddIdentity(graphene.Mutation):
    class Arguments:
        source = graphene.String()
        name = graphene.String()
        email = graphene.String()
        username = graphene.String()
        uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, source,
               name=None, email=None, username=None,
               uuid=None):
        identity = add_identity(source,
                                name=name,
                                email=email,
                                username=username,
                                uuid=uuid)
        id_ = identity.id
        uidentity = identity.uidentity

        return AddIdentity(
            uuid=id_,
            uidentity=uidentity
        )


class DeleteIdentity(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        unique_identity = graphene.Boolean()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, uuid):
        uidentity = delete_identity(uuid)

        return DeleteIdentity(
            uuid=uuid,
            uidentity=uidentity
        )


class UpdateProfile(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        data = ProfileInputType()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, uuid, data):
        uidentity = update_profile(uuid, **data)

        return UpdateProfile(
            uuid=uidentity.uuid,
            uidentity=uidentity
        )


class MoveIdentity(graphene.Mutation):
    class Arguments:
        from_id = graphene.String()
        to_uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, from_id, to_uuid):
        uidentity = move_identity(from_id, to_uuid)

        return MoveIdentity(
            uuid=uidentity.uuid,
            uidentity=uidentity
        )


class MergeIdentities(graphene.Mutation):
    class Arguments:
        from_uuid = graphene.String()
        to_uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, from_uuid, to_uuid):
        uidentity = merge_identities(from_uuid, to_uuid)

        return MergeIdentities(
            uuid=uidentity.uuid,
            uidentity=uidentity
        )


class Enroll(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        organization = graphene.String()
        from_date = graphene.DateTime(required=False)
        to_date = graphene.DateTime(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, uuid, organization, from_date=None, to_date=None):
        uidentity = enroll(uuid, organization,
                           from_date=from_date, to_date=to_date)
        return Enroll(
            uuid=uidentity.uuid,
            uidentity=uidentity
        )


class Withdraw(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        organization = graphene.String()
        from_date = graphene.DateTime(required=False)
        to_date = graphene.DateTime(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, uuid, organization, from_date=None, to_date=None):
        uidentity = withdraw(uuid, organization,
                             from_date=from_date, to_date=to_date)
        return Withdraw(
            uuid=uidentity.uuid,
            uidentity=uidentity
        )


class SortingHatQuery:

    organizations = graphene.Field(
        OrganizationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=OrganizationFilterType(required=False)
    )
    uidentities = graphene.Field(
        IdentityPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=IdentityFilterType(required=False)
    )
    transactions = graphene.Field(
        TransactionPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=TransactionFilterType(required=False)
    )
    operations = graphene.Field(
        OperationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=OperationFilterType(required=False),
    )

    def resolve_organizations(self, info, filters=None,
                              page=1,
                              page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                              **kwargs):
        query = Organization.objects.order_by('name')

        if filters and 'name' in filters:
            query = query.filter(name=filters['name'])

        return OrganizationPaginatedType.create_paginated_result(query,
                                                                 page,
                                                                 page_size=page_size)

    def resolve_uidentities(self, info, filters=None,
                            page=1,
                            page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                            **kwargs):
        query = UniqueIdentity.objects.order_by('uuid')

        if filters and 'uuid' in filters:
            query = query.filter(uuid=filters['uuid'])

        return IdentityPaginatedType.create_paginated_result(query,
                                                             page,
                                                             page_size=page_size)

    def resolve_transactions(self, info, filters=None,
                             page=1,
                             page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                             **kwargs):
        query = Transaction.objects.order_by('created_at')

        if filters and 'tuid' in filters:
            query = query.filter(tuid=filters['tuid'])
        if filters and 'name' in filters:
            query = query.filter(name=filters['name'])
        if filters and 'is_closed' in filters:
            query = query.filter(is_closed=filters['isClosed'])
        if filters and 'from_date' in filters:
            query = query.filter(created_at__gte=filters['from_date'])
        if filters and 'to_date' in filters:
            query = query.filter(created_at__lte=filters['to_date'])

        return TransactionPaginatedType.create_paginated_result(query,
                                                                page,
                                                                page_size=page_size)

    def resolve_operations(self, info, filters=None,
                           page=1,
                           page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                           **kwargs):
        query = Operation.objects.order_by('timestamp')

        if filters and 'ouid' in filters:
            query = query.filter(ouid=filters['ouid'])
        if filters and 'op_type' in filters:
            query = query.filter(op_type=filters['op_type'])
        if filters and 'entity_type' in filters:
            query = query.filter(entity_type=filters['entity_type'])
        if filters and 'target' in filters:
            query = query.filter(target=filters['target'])
        if filters and 'from_date' in filters:
            query = query.filter(timestamp__gte=filters['from_date'])
        if filters and 'to_date' in filters:
            query = query.filter(timestamp__lte=filters['to_date'])

        return OperationPaginatedType.create_paginated_result(query,
                                                              page,
                                                              page_size=page_size)


class SortingHatMutation(graphene.ObjectType):
    add_organization = AddOrganization.Field()
    delete_organization = DeleteOrganization.Field()
    add_domain = AddDomain.Field()
    delete_domain = DeleteDomain.Field()
    add_identity = AddIdentity.Field()
    delete_identity = DeleteIdentity.Field()
    update_profile = UpdateProfile.Field()
    move_identity = MoveIdentity.Field()
    merge_identities = MergeIdentities.Field()
    enroll = Enroll.Field()
    withdraw = Withdraw.Field()
