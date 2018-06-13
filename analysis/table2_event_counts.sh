echo "Wikipedia:"
echo -n "events: "
wc -l ../wiki/events-none/* | tail -n1
echo -n "unique events: "
cut -d';' -f4 ../wiki/events-none/* | sort | uniq | wc -l

echo "\nWikiNews"
echo -n "events: "
wc -l ../wikinews/events-none/* | tail -n1
echo -n "unique events: "
cut -d';' -f4 ../wikinews/events-none/* | sort | uniq | wc -l

echo "\nReuters"
echo -n "events: "
wc -l ../reuters/events-none/* | tail -n1
echo -n "unique events: "
cut -d';' -f4 ../reuters/events-none/* | sort | uniq | wc -l

echo "\nTotal"
echo -n "events: "
wc -l ../{wiki,wikinews,reuters}/events-none/* | tail -n1
echo -n "unique events: "
cut -d';' -f4 ../{wiki,wikinews,reuters}/events-none/* | sort | uniq | wc -l