# The Quick Version

```
>> python fin-cen-114.py /path/to/my.beancount --year 2017
Assets:AUS:CMC $11,295 ABC123
Assets:AUS:Cash $0 
Assets:AUS:Citibank $3,751 ABC456
Assets:AUS:First-State-Super $122,568 ABC789
...
```

Using this script means

1. You don't accidentally forget any accounts.
2. You don't have to remember/lookup/calculate the maximum account value in $USD.
3. You dont' have to lookup the account numbers of all your foreign accounts.

# FinCEN 114

FinCEN Report 114[1], or Report of Foreign Bank and Financial Accounts
(FBAR), is required to be filed every year by US persons (basically, US
citizen and residents) who hold a bank account overseas and whose aggregate
value of all foreign financial accounts exceeds $10,000 in any year.  You
have to list every foreign bank account, **along with the maximum account
value during the year**, the account number, the name of the institution,
and some other similar details.

For many US persons, this is not necessarily challenging to gather. If you
have a lot of accounts and the value of those accounts has varied substantially
then it becomes a little bit harder.

Of course, if you're using beancount[2] then it **already** has all the
information needed for filing FinCEN 114. This script does the work of
gathering it all together for you.

# Account numbers

If you add metadata on the account opening directive then this script will
remind you of what that is. This makes filling in the FinCEN 114 easier,
since you don't have to hunt down all the account numbers yourself. You can
specify the metadata like so:

```
2014-04-08 open Assets:AUS:Citibank AUD
        account-number: 431411339
```

If you prefer to use a different metadata keyword, you can specify that with
the ```--meta-account-number``` option.

# Price map warning

The results you get will only be as good as your price data. If you try to
run this for the year 2010 but haven't given beancount any price directives
for the year 2010, then the results will be nonsensical. (You will usually get
a value of $0 for the account, regardless of what is in it.)

# Option summary

* ```---year``` the calendar year to use
* ```--only-account``` Instead of listing all accounts, you can specify which accounts you care about.
* ```--meta-account-number``` This is the metadata on the account opening directive that includes the account number. By default it will look for *account-number*

[1]: https://bsaefiling.fincen.treas.gov/NoRegFBARFiler.html
[2]: https://bitbucket.org/blais/beancount/overview