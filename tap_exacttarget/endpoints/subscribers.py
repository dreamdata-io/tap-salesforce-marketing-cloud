import FuelSDK
import copy
import singer

from tap_exacttarget.client import request
from tap_exacttarget.dao import DataAccessObject, exacttarget_error_handling
from tap_exacttarget.pagination import get_date_page, before_now, increment_date

from tap_exacttarget.state import (
    incorporate,
    save_state,
    get_last_record_value_for_table,
)

LOGGER = singer.get_logger()


class SubscriberDataAccessObject(DataAccessObject):

    TABLE = "subscriber"
    KEY_PROPERTIES = ["ID"]
    REPLICATION_METHOD = "INCREMENTAL"
    REPLICATION_KEYS = ["CreatedDate"]

    def parse_object(self, obj):
        to_return = obj.copy()

        if "ListIDs" in to_return:
            to_return["ListIDs"] = [
                _list.get("ObjectID") for _list in to_return.get("Lists", [])
            ]

        if "Lists" in to_return:
            del to_return["Lists"]

        if to_return.get("Addresses") is None:
            to_return["Addresses"] = []

        if to_return.get("PartnerProperties") is None:
            to_return["PartnerProperties"] = []

        return super().parse_object(obj)

    def sync_data(self):
        start = get_last_record_value_for_table(
            self.state, self.__class__.TABLE, self.config
        )
        unit = {"days": 7}
        while before_now(start):
            search_filter = get_date_page(
                self.__class__.REPLICATION_KEYS[0], start, unit
            )
            end = increment_date(start, unit)
            stream = request(
                "Subscriber",
                FuelSDK.ET_Subscriber,
                self.auth_stub,
                search_filter,
                batch_size=self.batch_size,
            )

            for subscriber in stream:
                subscriber = self.filter_keys_and_parse(subscriber)

                self.write_records_with_transform(
                    subscriber, self.catalog, self.__class__.TABLE
                )
            self.state = incorporate(
                self.state,
                self.__class__.TABLE,
                self.__class__.REPLICATION_KEYS[0],
                start,
            )
            save_state(self.state)
            start = end
            end = increment_date(end, unit)

    # fetch subscriber records based in the 'subscriber_keys' provided
    @exacttarget_error_handling
    def pull_subscribers_batch(self, subscriber_keys):
        if not subscriber_keys:
            return

        table = self.__class__.TABLE
        _filter = {}

        if len(subscriber_keys) == 1:
            _filter = {
                "Property": "SubscriberKey",
                "SimpleOperator": "equals",
                "Value": subscriber_keys[0],
            }

        elif len(subscriber_keys) > 1:
            _filter = {
                "Property": "SubscriberKey",
                "SimpleOperator": "IN",
                "Value": subscriber_keys,
            }
        else:
            LOGGER.info("Got empty set of subscriber keys, moving on")
            return

        stream = request(
            "Subscriber",
            FuelSDK.ET_Subscriber,
            self.auth_stub,
            _filter,
            batch_size=self.batch_size,
        )

        catalog_copy = copy.deepcopy(self.catalog)

        for subscriber in stream:
            subscriber = self.filter_keys_and_parse(subscriber)

            self.write_records_with_transform(subscriber, catalog_copy, table)
