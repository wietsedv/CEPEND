echo "Wikipedia:"
for f in `ls -1 ../wiki/plaintext | xargs`; do echo -n "$f " && ls -1 $f | wc -l; done

echo "\nWikiNews"
for f in `ls -1 ../wikinews/plaintext | xargs`; do echo -n "$f " && ls -1 $f | wc -l; done

echo "\nReuters"
for f in `ls -1 ../reuters/plaintext | xargs`; do echo -n "$f " && ls -1 $f | wc -l; done
