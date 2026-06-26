import datetime

# 1
now = datetime.datetime.now()
day = datetime.timedelta(days = 5)

future = now + day

print(future)

# 2
today = datetime.datetime.today()
yesterday = today - datetime.timedelta(days = 1)
tomorrow = today + datetime.timedelta(days = 1)

print(yesterday)
print(today)
print(tomorrow)

# 3
now = datetime.datetime.now()
print(now.strftime("%Y-%m-%d %H:%M:%S"))

# 4
now = datetime.date(2025, 5, 30)
then = datetime.date(2025, 5, 29)
ans = now - then
ans = ans.days * 24 * 60 * 60
print(ans)