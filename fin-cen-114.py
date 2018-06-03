#!/usr/bin/env python

import logging
import sys
import functools
import math
import collections
import datetime
import beancount.loader
import beancount.utils
import beancount.core
import beancount.core.realization
import beancount.core.data
import beancount.parser
from beancount.utils.date_utils import iter_dates

def get_date(p):
    if isinstance(p, beancount.core.data.Posting):
        return p.date
    elif isinstance(p, beancount.core.data.TxnPosting):
        return p.txn.date
    else:
        raise Exception("Not a Posting or TxnPosting", p)

def only_postings(p):
    if isinstance(p, beancount.core.data.Posting):
        return True
    elif isinstance(p, beancount.core.data.TxnPosting):
        return True
    else:
        return False

def this_year(year, p):
    return get_date(p).year == year

def add_position(p, inventory):
    if isinstance(p, beancount.core.data.Posting):
        inventory.add_position(p)
    elif isinstance(p, beancount.core.data.TxnPosting):
        inventory.add_position(p.posting)
    else:
        raise Exception("Not a Posting or TxnPosting", p)

def start_of_year_inventory(year, postings):
    balance = beancount.core.inventory.Inventory()
    for p in filter(only_postings, postings):
        if get_date(p).year < year:
            add_position(p, balance)
    return balance

def iter_year(year, account_postings, inventory, price_map):
    start_of_year = datetime.date(year, 1, 1)
    end_of_year = datetime.date(year+1, 1, 1)

    filter_year = functools.partial(this_year, year)

    postings = filter(only_postings, account_postings)
    postings = filter(filter_year, postings)
    txn = next(postings, None)
    for date in iter_dates(start_of_year, end_of_year):
        while txn and get_date(txn) <= date:
            add_position(txn, inventory)
            txn = next(postings, None)
        yield date, inventory.reduce(beancount.core.convert.convert_position, 'USD', price_map, date)

def get_account_number(account, keys):
    for k in keys:
        if k in account.meta.keys():
            return account.meta[k]
    return ''

def fmt_d(n):
    return '${:,.0f}'.format(n)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Summarise account information for FinCEF 114 filing."
    )
    parser.add_argument('bean', help='Path to the beancount file.')
    parser.add_argument('--year', type=int, help='Which year to summarise.', required=True)
    parser.add_argument('--only-account', action='append', help='Only calculate for specified account(s).')
    parser.add_argument('--meta-account-number', default=['account-number'], action='append', help='Metadata key(s) containing account numbers.')
    args = parser.parse_args()

    entries, errors, options = beancount.loader.load_file(args.bean, logging.info, log_errors=sys.stderr)

    account_types = beancount.parser.options.get_account_types(options)
    open_close = beancount.core.getters.get_account_open_close(entries)

    filter_fun = functools.partial(beancount.core.account_types.is_account_type, account_types.assets)
    sortkey_fun = functools.partial(beancount.core.account_types.get_account_sort_key, account_types)

    # We only want Asset accounts and we want them sorted for us
    items = open_close.items()
    accounts_filtered = filter(lambda entry: filter_fun(entry[0]), items)
    accounts_sorted = sorted(accounts_filtered, key=lambda entry: sortkey_fun(entry[0]))

    realized_accounts = beancount.core.realization.postings_by_account(entries)
    price_map = beancount.core.prices.build_price_map(entries)

    for account, (open, close) in accounts_sorted:
        if args.only_account and account not in args.only_account: continue

        open_year = open.date.year if open else -math.inf
        close_year = close.date.year if close else math.inf

        # Only do this for accounts that were open during the year in question
        if open_year <= args.year <= close_year:
            account_postings = realized_accounts[account]
            inventory = start_of_year_inventory(args.year, account_postings)
            
            # now we need to iterate day-by-day through the year. We add any new
            # postings and then reduce to a price. Then see if that is the highest
            # price seen so far....
            max_value = 0
            for (date, balance) in iter_year(args.year, account_postings, inventory, price_map):
                usd_value = balance.get_currency_units('USD')
                max_value = max(max_value, int(usd_value.number))

            account_number = get_account_number(open, args.meta_account_number)
            print(account, fmt_d(max_value), account_number)