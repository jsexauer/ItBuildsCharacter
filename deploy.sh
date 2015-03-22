git checkout master
git pull
buildozer android debug deploy run
cp ./bin/ItBuildsCharacter-0.0.1-debug.apk ../latest_test.apk
git checkout gh-pages
cp ../latest_test.apk ./apk/latest_test.apk
git commit -a -m "Updated apk"
git push

