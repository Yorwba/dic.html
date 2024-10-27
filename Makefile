#   dic.html puts simple dictionary search into one self-contained HTML file.
#   Copyright 2024 Yorwba

#   dic.html is free software: you can redistribute it and/or
#   modify it under the terms of the GNU Affero General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.

#   dic.html is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with dic.html.  If not, see <https://www.gnu.org/licenses/>.

.SECONDARY:

dics/%.db:
	wget --timestamping --directory-prefix=dics/ \
		https://digitalnk.com/dics/$*.db

tmp/%.packed: dics/%.db packed_db.py
	mkdir -p tmp/
	./packed_db.py $< $@

html/%.html: tmp/%.packed template.html.head template.html.tail
	mkdir -p html/
	cat template.html.head $< template.html.tail > $@
