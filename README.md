# dic.html

**dic.html** puts simple dictionary search into one self-contained HTML file.

It is designed to work with dictionary database files as used by the
[digitalprk/dicrs](https://github.com/digitalprk/dicrs) project.
([Digitial NK's awesome writeup](https://digitalnk.com/blog/2020/05/08/porting-north-korean-dictionaries-with-rust/)
about extracting these files is worth a read.)

An
[online demo of the Korean-English dictionary](https://yorwba.github.io/dic.html/)
is available. (**Warning**: large file! Download and use offline.)

## Usage

```bash
make html/KEEK.html
```
to create the Korean-English/English-Korean dictionary HTML file.

Names of other
[files provided by Digital NK](https://github.com/digitalprk/dicrs?tab=readme-ov-file#dictionaries)
also work.

If you want to make your own dictionary file,
create a SQLite databases with a table conforming to the following schema:
```sql
CREATE TABLE dictionary (word text, definition text);
```
and fill it with entries.

Then place it at `dics/$YOUR_DICTIONARY_FILE.db` and run
```bash
make html/$YOUR_DICTIONARY_FILE.html
```

## How it works and why it works this way

### One file to rule them all

In theory, it would be possible to use the SQLite dictionaries directly with
[SQLite compiled to WebAssembly](https://sqlite.org/wasm),
*but* it seems like you would then end up with multiple files,
and having everything inside a single HTML file was very important to me.

Why a single file?
Because locked-down mobile devices *may* generously allow opening one HTML file,
but said file will be prevented from loading any other local resources,
so that it cannot steal the secret data right next to it in your downloads folder.

So the dictionary application needs to be one single file
to work offline with minimal fuss.

### Zero copies

The next big obstacle is memory use.
If you encode a large amount of data as a JSON object
and put it directly inside your JavaScript code,
it will take up memory in triplicate:

1. Firstly, as part of the original document.
2. Secondly, as parsed JavaScript code.
3. Thirdly, as the pile of nested objects that JavaScript code evaluated to.

Therefore:

1. There are no nested objects.
   The search index uses a flat suffix array, not a naive suffix tree.
   Everything is packed into a single string.
2. This string is not embedded in JavaScript code,
   but in a separate HTML element.
3. When the encoded data is assigned to an HTML attribute,
   it doesn't even count towards the document memory
   according to the Firefox DevTools' Memory tab.
   (This might be a Firefox bug. Oops!)

The actual implementation details involve pointer arithmetic
and digging individual ≈15.75-bit values out of an UTF-16 string
with `charCodeAt()`,
but it works, somehow!
