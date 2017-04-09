
# Clocktails - A Mastodon Bot

Because its always time for cocktails somewhere.

A super simple bot that simply finds a town where it is shortly 5pm local time,
waits until 5pm arrives and then toots a reminder that it's time for drinks there.

### To install

- pip install Mastodon.py
- Create secrets/secrets.txt (see secrets/README_secrets)
- Use cron to run clocktails.py every hour a few minutes before the hour and half hour.

I use:

```
29,59 * * * * ( cd $HOME/Projects/clocktails; /usr/bin/python clocktails.py >> clocktails.log )
```
