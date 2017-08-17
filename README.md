The server instance is running at:
http://52.91.37.204:8080/

The webserver is in frontend.py. The backend is in crawler.py.

The max connections has not changed since lab2. This makes sense because it is
not bound by time or disk usage. The max number of requests per second has gone
down and the latency has gone up, corresponding to the increased amount of work
needed to query the database for results on each request. Disk usage expectedly
went up, but both results appear anomalous, and likely are unrelated to the
operation of the web service.

Lab 2

Max connections: 1015
Max rps: 200
Average latency: 86.72ms
99th percentile latency: 1.17s
Utilization: 
    cpu: 98%
    disk: 7629kB/s
    net: 1085kB/s


Lab 3

Max connections: 1015
Max rps: 141
Average latency: 208.73ms
99th percentile latency: 1.92s
Utilization
    cpu: 86%
    disk: 11MB/s
    net: 535kB/s


