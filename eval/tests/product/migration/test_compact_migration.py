"""Installed catalog diagnosis and physical copy/adoption preserve source authority and evidence."""
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[4]
NEXT_TASK_CHECK = 'python3 -I -c \'from pathlib import Path; p=Path("owned/check-observed.txt"); p.parent.mkdir(exist_ok=True); p.write_bytes(b"adopted-check\\n")\''
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'eval/tests/product/lint/rows'))
from maintaining.install_root import current_root
import test_lint_rows as base

PROVENANCE = json.loads('{"groups":[{"source":"G","heading":"v8.4 → v9.0 checklist","start":44,"end":74,"sha256":"f3250ed12d9cb41ca0ceb6fb888eb9bb0ea991c7fbfd2dffba58f16c09ea9762","families":["I","S","B","A","O","M","Z"]},{"source":"G","heading":"v9.2 → v9.3 checklist","start":75,"end":85,"sha256":"8d2d2234d2072d2b7a50c65ab1d6e1e7bc5947f11c99160c303b5b164e9a6770","families":["W","O"]},{"source":"G","heading":"v9.3 → v10.0 checklist","start":86,"end":102,"sha256":"54030878658f17ff3931632bc0af31601fd4aef20df8da16e80125c86c16be6c","families":["I","W","I","E","J"]},{"source":"G","heading":"v10.0 → v10.1 checklist","start":103,"end":117,"sha256":"0c51228107207d4e4fc566a8ab9ceb662da0a1ca1a5c5ecfad8dbfb22f052363","families":["S","E","E","E","H","V","W","B","J"]},{"source":"G","heading":"v10.1 → v10.2 checklist","start":118,"end":134,"sha256":"34b3b20b638486863cede76af6982ec6c78559d750bd5beed7c26e00f11c916d","families":["P","R","R","R","B","B","B","V","A","O","Z"]},{"source":"H","heading":"v9.2.0 → v9.2.1 checklist","start":30,"end":46,"sha256":"977e55c3247158261089ca32434a98dff16d766910c1dd2ac053355c445ce3dc","families":["P","W","Z"]},{"source":"H","heading":"v9.1 → v9.2 checklist","start":47,"end":69,"sha256":"99acf5be566f9670c74a4aee924af94be768ccda1edc08ef1cc6219715100122","families":["P","B","N","Q","Z"]},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","start":70,"end":91,"sha256":"cdc27f4cb793a4f3ea0b5a2054dba26720459cc6c51ed29e6a85a5bbb5db0c78","families":["P","E","M","J","W","Z"]},{"source":"H","heading":"v9.0 → v9.1 checklist","start":92,"end":125,"sha256":"3ba4af9549077780aa9030ba2c595863cfcd65195090ba5a46e570abed5bed47","families":["P","V","R","R","H","E","H","Z"]},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","start":126,"end":156,"sha256":"194e3f1a836a442b09323a2df61c710a91b367b442b084770c82bc0c1a148bd6","families":["P","M","M","B","Z","E"]},{"source":"H","heading":"v8.4.0 → v8.4.1 checklist","start":157,"end":182,"sha256":"8ce9763cdc5a47b662f49963aa82e60b7577471d4445a274f88d5109f7bddce0","families":["P","V","B","B","Z"]},{"source":"H","heading":"v8.3 → v8.4 checklist","start":183,"end":224,"sha256":"20c4d59177683dc18730eb2f070dca891f263a9edc391029ab10ebb4afb7d27d","families":["P","A","S","V","Z"]},{"source":"H","heading":"v8.2 → v8.3 checklist","start":225,"end":248,"sha256":"00cdf4ef04195b5cfeacb16378fffc7368d6039fb85c03b5e62ba8cef6d24b02","families":["P","E","E","Z"]},{"source":"H","heading":"v8.2.0 → v8.2.1 checklist","start":249,"end":263,"sha256":"3732db5114badd30e722268c126eb1f4f5b43c50609129a2d34ec07b136763d4","families":["P","E","Z"]},{"source":"H","heading":"v8.1 → v8.2 checklist","start":264,"end":348,"sha256":"de84340cfe893cca5fd43f1a03004cfb53406c7284056a70a1ff88465a546d48","families":["P","B","A","B","H","Z"]},{"source":"H","heading":"v8.0 → v8.1 checklist","start":349,"end":377,"sha256":"893cdce7ca2ebedcd9c7997eba390e0f368a2acb914d89336e0f65f2c6608f2c","families":["P","A","B","V","Z"]},{"source":"H","heading":"Historical migration shape","start":378,"end":390,"sha256":"b31bcbcbbb59981b54bb33894eb1d4b8ac248fa7795b3592cb1a71ab1cf0fb27","families":["S","P","A","B","B","V"]},{"source":"H","heading":"v7.3 → v8.0 checklist","start":391,"end":441,"sha256":"d260fa2a4ab22cabccde5bf1e233464d77209e6caeb749fe6e4c3db56572677e","families":["P","P","B","A","E","Z","Z"]},{"source":"H","heading":"v7.0 → v7.1 checklist","start":442,"end":452,"sha256":"18b80c9831567412ac8cc4ebb93facc89750343be679d86e73c56ddf9be80219","families":["I","I","A","I","E","Z"]},{"source":"H","heading":"v7.1 → v7.2 checklist","start":453,"end":485,"sha256":"fb2c8b3ce31c5dfdc4c1877980c488a7e072f81d891c1ec065226ecf941c7038","families":["P","E","E","E","E","V","Z"]},{"source":"H","heading":"v7.2 → v7.3 checklist","start":486,"end":507,"sha256":"5e009888f48bdca9702cdd3358b8604dab9ef8e739f1d1936f6cbdfcc9ba31af","families":["B","B","E","B","Z"]},{"source":"H","heading":"v6.1 → v7.0 checklist","start":508,"end":517,"sha256":"a657e3f47f34991b1d4e974e8849daba67296de861e2113f802d6780c4b6684b","families":["A","I","A","Z","V"]},{"source":"H","heading":"v6.0 → v6.1 checklist","start":518,"end":525,"sha256":"5266ccfc6ed22bcb711e25180860d7f8c3b928ecfc811c16610021d1dcdacae7","families":["E","E","Z"]},{"source":"H","heading":"v5.6 → v6.0 checklist","start":526,"end":533,"sha256":"d968d86f42b8e2756f26bf98bfa5759c823b8f6cee51e8e6801a3e741898412c","families":["E","E","Z"]},{"source":"H","heading":"v5.5 → v5.6 checklist","start":534,"end":542,"sha256":"fe0f13addf35c6bb0c9cca8350f311e1a1244ff8dff241cae1e25c060cf3336e","families":["R","H","O","Z"]},{"source":"H","heading":"v5.4 → v5.5 checklist","start":543,"end":550,"sha256":"007cdbe9e9a7075e4501aa8f573c73e9b637f62b4ed789f82feae96d43d49ca9","families":["H","B","Z"]},{"source":"H","heading":"v5.3 → v5.4 checklist","start":551,"end":557,"sha256":"966c0f1c988358422f0638e7f149c3b9ed90d2d59ea5705a0c5497bbc074d2c2","families":["V","Z"]},{"source":"H","heading":"v5.2 → v5.3 checklist","start":558,"end":582,"sha256":"0e5e62a55da0a1cbac056153ac98b242c3ef19a5540e13d6b5385015224f450b","families":["B","B","B","B","V","Z"]},{"source":"H","heading":"v5.1 → v5.2 checklist","start":583,"end":609,"sha256":"bd6b5c55d20b485634c3033b96d57725142ad9685dcf1e4139bae6f2981e6c59","families":["E","M","M","V","B","Z"]},{"source":"H","heading":"v5.0 → v5.1 checklist","start":610,"end":620,"sha256":"93a0ee99428f07b5911b1b950cae0155c7667a43310b96ba10856d2dcb827ba9","families":["O","B","O","O","B","Z"]},{"source":"H","heading":"v4.4 → v5.0 checklist","start":621,"end":628,"sha256":"02b60b94e4dcdd8ae0e46e85636faa19459fa1c839fd15f60d375b6f5a6239f2","families":["E","V","Z"]},{"source":"H","heading":"v4.3 → v4.4 checklist","start":629,"end":635,"sha256":"d6cd2ab8c07843c44217b14cefa1a266b860d89d4b10c9ed7040c448163afff7","families":["A","Z"]},{"source":"H","heading":"v4.2 → v4.3 checklist","start":636,"end":643,"sha256":"57f6375b0aa2dcbd53acd08f3188a960f99e4971a07320d456a99b44229bebe8","families":["E","E","Z"]},{"source":"H","heading":"v4.1 → v4.2 checklist","start":644,"end":650,"sha256":"3ad5fe7a229550b866b6f5a2380144517322e110a53c88f906a24d875a281930","families":["E","Z"]},{"source":"H","heading":"v4.0 → v4.1 checklist","start":651,"end":658,"sha256":"6539e5d712968362e50050b6596eadb55d260c79bb3ef3b2656ba90521c21943","families":["I","O","Z"]},{"source":"H","heading":"v3.4 → v4.0 checklist","start":659,"end":671,"sha256":"e21ea3282e6464d6f8e042cd5f4a8ff0667f951e335b6f6055e00592b350ac40","families":["B","B","O","A","M","V","O","Z"]},{"source":"H","heading":"v3.3 → v3.4 checklist","start":672,"end":680,"sha256":"306616676f4c879a59d8e5808a3fe456d392dd264318bf1f2144ef8a12a41289","families":["A","O","V","Z"]},{"source":"H","heading":"v3.2 → v3.3 checklist","start":681,"end":688,"sha256":"1217f31ffe2e6ab4cae08e05c3607d4e1350c2dae0de3cd02346808d89ccc4f7","families":["M","R","Z"]},{"source":"H","heading":"v3.0 → v3.1 checklist","start":689,"end":699,"sha256":"a1b07b61e3ea4562b5628d81006b5fb571f6cc5fa798606774c5bfa9812b058d","families":["B","E","E","B","E","Z"]},{"source":"H","heading":"Artifact renames","start":700,"end":708,"sha256":"48f6cef548ed868b84dc15386aae2f2e3a9161e9a721a18d2b75a3cdf6fb9203","families":["S","S","P","Z"]},{"source":"H","heading":"Historical structural conformance","start":709,"end":718,"sha256":"bfb53a7a828066b6a8823b87b89ee972ec645d38d0f1fa711f72a4e63fc258b1","families":["S","A","A","B"]},{"source":"H","heading":"Historical citations","start":719,"end":725,"sha256":"144fcccfd7d2114273ad9ec7d4fed0873bc41742fea338458b0c1d1da5d61e77","families":["B"]},{"source":"H","heading":"v2.1 → v3.0 checklist","start":726,"end":739,"sha256":"cd27b560ccbf8f66e81747988dc3e41f46275a510af45717d7a2c1556c7cf330","families":["B","E","B","V","B","M","E","M","Z"]},{"source":"H","heading":"v2.0 → v2.1.0 checklist","start":740,"end":752,"sha256":"71ed780135d1a4bd16402b3eec44d718e095eb6859da58d40fc5734805e6b5b6","families":["A","B","B","B","O","Q","M","V","Z"]}],"items":[{"source":"G","heading":"v8.4 → v9.0 checklist","index":1,"sha256":"e48ac9cad96aee8575d519f7c00b1b1ebeebbf3bdaf8bb81b18d68bfde0f8175","family":"I"},{"source":"G","heading":"v8.4 → v9.0 checklist","index":2,"sha256":"c6fb4a6a505b26fca7ccfc3c4d7614825967d40c63d152d2bdce1fd3fd5a9cbb","family":"S"},{"source":"G","heading":"v8.4 → v9.0 checklist","index":3,"sha256":"1713c32c74688d0b67bce7d15dd5048f6ef9fdd5bfc47d1e0b60f18829637b7d","family":"B"},{"source":"G","heading":"v8.4 → v9.0 checklist","index":4,"sha256":"89d23ea5ec531b5a652f36b5b84bd5b0558f74ff6c6d3dba49b0effcd07921c0","family":"A"},{"source":"G","heading":"v8.4 → v9.0 checklist","index":5,"sha256":"8b5e06d7d7726640adf89d77897e018f375b20a8e77c93e3b6aa3aba4a2b4b1b","family":"O"},{"source":"G","heading":"v8.4 → v9.0 checklist","index":6,"sha256":"c6a1712863c548be7f62264029a25ae9bb68a2c1a34caf7aa7d0081f4de0fd43","family":"M"},{"source":"G","heading":"v8.4 → v9.0 checklist","index":7,"sha256":"f99e7121677e50b56a281860330ca50ddc10b5964bc7adb0562f5453b7986e75","family":"Z"},{"source":"G","heading":"v9.2 → v9.3 checklist","index":1,"sha256":"a6431c992b5ee0c3d19679ac299dae2c0c4fca30225b378190d8e271a7caafce","family":"W"},{"source":"G","heading":"v9.2 → v9.3 checklist","index":2,"sha256":"c9d15927a8fbee1f51a1d29c05dc582242405fc368aef15e4b6dc2794dad6144","family":"O"},{"source":"G","heading":"v9.3 → v10.0 checklist","index":1,"sha256":"a8b0dca5cb44c8f6030d607c30563adaf613c9013a91091fe356fb467640f3c4","family":"I"},{"source":"G","heading":"v9.3 → v10.0 checklist","index":2,"sha256":"885e9961d78a6c3c4cb674f5643e2e2b36e75b2a1b432a2c222d9f484e0154a2","family":"W"},{"source":"G","heading":"v9.3 → v10.0 checklist","index":3,"sha256":"2f1b2cbcfdb96435a6eb9729141196c485cbf1dfc72eac31ae151e4756b815fe","family":"I"},{"source":"G","heading":"v9.3 → v10.0 checklist","index":4,"sha256":"8a028af28afd5546c866991b5496575138db6b807a2e0b02444a4d2078eae8a0","family":"E"},{"source":"G","heading":"v9.3 → v10.0 checklist","index":5,"sha256":"4c691434eb46a6035599510865be39b07966c3cb508a9ab08b39e706bef66ca6","family":"J"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":1,"sha256":"b7ea575e192ac707483e70ae2c8a5aab7ce6ddca4cfbc995714580571daa9c15","family":"S"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":2,"sha256":"5309d4726f7c7ca1bc31afda8102b0412300d9bb94fb1932b05ed5fc161347b4","family":"E"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":3,"sha256":"ca0ed70e6073f8053a27d53fbb33285f91580da4024bbec3acc48baf1163ba0f","family":"E"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":4,"sha256":"37b6fddd36bf77096b50daa6832e8745af0be10097a7f1460d83d44131745ec6","family":"E"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":5,"sha256":"541aa07e0c68de889ba49f7729333031b9be43d44480123c27ec76029978b522","family":"H"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":6,"sha256":"1a067159c67937e8841d29be5067c4953209bf99ec52e71380045ded248b8131","family":"V"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":7,"sha256":"cff83ace0fbea9c997bf4e0c36e952da532537ed96444c5b3bb1a17629eec53a","family":"W"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":8,"sha256":"9d32511ba6dfce0322234fa81fb5fdf25bdfe1fe08ed4261191ef3591dd14963","family":"B"},{"source":"G","heading":"v10.0 → v10.1 checklist","index":9,"sha256":"dbec4e139ea395f2698434b98f7aae6a8f80b5344d985cd0257638439f7bf192","family":"J"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":1,"sha256":"0d70c7a23114068258c2915a52543294ef89509a93f53a6e1eb6aa72e02d6791","family":"P"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":2,"sha256":"fd33c2a4ffe8a6d897624b2967b0630b6aa082dee1204c56ad85239b5e8c4219","family":"R"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":3,"sha256":"0c82376a76ac9ffa98f8d414414e529490172eb2c9a9bf0519c617717b9e48bb","family":"R"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":4,"sha256":"9fcacfdc1cd12b8eb2f113bd3c8ed850af4500f35e0777846099fef1bdd57f44","family":"R"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":5,"sha256":"4c586f300f4ddfdd143d4de9b708f1307621123f71b658bd90eed055daaedfae","family":"B"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":6,"sha256":"d20a5d18a06f853619742be8c88a616a1b5070b672f7c0c8b69df83fe227cf68","family":"B"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":7,"sha256":"30c94110849cf98060e960645b0e8e7eb01e99553ee0c4dc7665a0ae86ced900","family":"B"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":8,"sha256":"c79ad34427410ab5f76c46d24f6f13c32605f5c77b3f6f3f233b5ef7f2e384aa","family":"V"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":9,"sha256":"a83d63d9519e7911a572d9af88030513c8fe3ed01af8efb8751acba0bd46f331","family":"A"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":10,"sha256":"a799fa9834844b715d8aa15c5278a8d128d63f71d7b1fa4b27d2b5894cc72791","family":"O"},{"source":"G","heading":"v10.1 → v10.2 checklist","index":11,"sha256":"294c5f3591670673ae7e1fa86f8fe8c82e377d9960516e370f6ed8bcdfebc1a8","family":"Z"},{"source":"H","heading":"v9.2.0 → v9.2.1 checklist","index":1,"sha256":"523a9ee7e919934eba84b15494a9c269afb47be507a836d3562cab0ba7f106e3","family":"P"},{"source":"H","heading":"v9.2.0 → v9.2.1 checklist","index":2,"sha256":"f4ed8d68b298fc69792fd7b336ceaab98c35849860cc32290e591222b24ff585","family":"W"},{"source":"H","heading":"v9.2.0 → v9.2.1 checklist","index":3,"sha256":"a3f9a124f563a5166a8e8ca7db07982a7c8d23fa12d5c7cacd3e314df51a96ec","family":"Z"},{"source":"H","heading":"v9.1 → v9.2 checklist","index":1,"sha256":"523a9ee7e919934eba84b15494a9c269afb47be507a836d3562cab0ba7f106e3","family":"P"},{"source":"H","heading":"v9.1 → v9.2 checklist","index":2,"sha256":"c99a06d23822fcd9b6d3bf0feb1dfb9eb0df40449f754e1dc0981b758c091628","family":"B"},{"source":"H","heading":"v9.1 → v9.2 checklist","index":3,"sha256":"c8b8f7afbe4f96da4d93cc85af16e084402e6b0e51507d267a686b1a8fc3906f","family":"N"},{"source":"H","heading":"v9.1 → v9.2 checklist","index":4,"sha256":"47e7640acd6eea3aa17d7ed4cc977a561a83284ca2f5cc20441d7d0eafed6421","family":"Q"},{"source":"H","heading":"v9.1 → v9.2 checklist","index":5,"sha256":"f58f5471f65ec5b226b1d9bc0e1010f21d8f38ed36cc9f8d13ad1e4657e70b58","family":"Z"},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","index":1,"sha256":"523a9ee7e919934eba84b15494a9c269afb47be507a836d3562cab0ba7f106e3","family":"P"},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","index":2,"sha256":"577d3e722302e6ac817435105adf42cb831e0aada9972a1cc488912a0dbc4e11","family":"E"},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","index":3,"sha256":"345682d36dd379950b25cf464795f44d4750e78864acfcbce2a2c320cce06648","family":"M"},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","index":4,"sha256":"342dca62b05155d2becce2de6a7e4eca51082d7043c7c0dedeb326347717dbd1","family":"J"},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","index":5,"sha256":"ca0e646718754d5e540ebf963ac37e135216960860aefc04a3ac5b26d27d92ee","family":"W"},{"source":"H","heading":"v9.1.0 → v9.1.1 checklist","index":6,"sha256":"cf47541329dd7da80065183cf4b596631546b4d80fa7abe81dcd29c3a3289622","family":"Z"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":1,"sha256":"523a9ee7e919934eba84b15494a9c269afb47be507a836d3562cab0ba7f106e3","family":"P"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":2,"sha256":"847db421fac45c5f5682f4687064868eb7e4b70542284a029f554245b4cee365","family":"V"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":3,"sha256":"3824d0579d60213f75646ffaf63e3809c6893f124736a20010f6c473c979c72d","family":"R"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":4,"sha256":"ac9731912f707238a08465b2b80c4e46653046baea73dde6d63985ff4dc46b1c","family":"R"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":5,"sha256":"ed2a8ba0c20248494ab8453247ee460b36eea20266a81e0ce209792c597f0cd8","family":"H"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":6,"sha256":"67c3bb981aedc00ee2135a591f6af9aff6c345421a681aab246cf72f1baff023","family":"E"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":7,"sha256":"486d7d3a8bb81851a54ad39e09743a7317233d4cb745d2428c81e7f7f7a4fb9f","family":"H"},{"source":"H","heading":"v9.0 → v9.1 checklist","index":8,"sha256":"b5f165b2d7ea31cf3f1d7f13f45df41e7bd7d5ede471ffb44c24eda5e7f01fde","family":"Z"},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","index":1,"sha256":"60c8164a8ad3bea96e4224aa57e535141c82ab6b8ef4a298d0ec2fe3913b9c14","family":"P"},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","index":2,"sha256":"7f80b0636f85fe766a6e83cabeab002c7810e227bf3db9019a841efe08a23b88","family":"M"},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","index":3,"sha256":"2e872a37eae81d73e0fce6d15f77775d663f5575ab36011c521485f83a1365ab","family":"M"},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","index":4,"sha256":"b128944586fc03759631518a848332815531cc65316aeb179356c4d3119e76ed","family":"B"},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","index":5,"sha256":"3f8a1300159294930666201509805d0fdd5e7777306b2b2f4596ef2a577b1912","family":"Z"},{"source":"H","heading":"v9.0.0 → v9.0.1 checklist","index":6,"sha256":"5b5f0f615f8a3e21f25fefdfb3dc1a962ce38bf8d35281bf42ca2efb6880aab7","family":"E"},{"source":"H","heading":"v8.4.0 → v8.4.1 checklist","index":1,"sha256":"4fb9036f1bdbabf14a859dec1abc9a98d07ffa5bb74c79044e3789521b4c8f36","family":"P"},{"source":"H","heading":"v8.4.0 → v8.4.1 checklist","index":2,"sha256":"16f99673c3932a95082d7637a92774027d98d1dd29b843f2b7f63f44a0405425","family":"V"},{"source":"H","heading":"v8.4.0 → v8.4.1 checklist","index":3,"sha256":"946e6528627c31c0fbac63a1db0895e187ed26091487284c35925fdfb9d09003","family":"B"},{"source":"H","heading":"v8.4.0 → v8.4.1 checklist","index":4,"sha256":"fe223b4bc2880af1d282d77199dd32a488593ce60fda7af882367a615206dcde","family":"B"},{"source":"H","heading":"v8.4.0 → v8.4.1 checklist","index":5,"sha256":"7cc9949f1e6cbb8d361bda707b06443ddecfab994b78e730be9e8e8fed0ceca2","family":"Z"},{"source":"H","heading":"v8.3 → v8.4 checklist","index":1,"sha256":"eff7d03b4ca31547ff1a1b4c64ef16e9ee958744166222e7f6d67d0876166565","family":"P"},{"source":"H","heading":"v8.3 → v8.4 checklist","index":2,"sha256":"6475f0d2fdfd5f1602225ba9c71634653035f674dc0440b4b18f267d09bff67b","family":"A"},{"source":"H","heading":"v8.3 → v8.4 checklist","index":3,"sha256":"b10a793f612a786c928931ea5646b01f65e0c2be155c8b9ce8b170e76368bf01","family":"S"},{"source":"H","heading":"v8.3 → v8.4 checklist","index":4,"sha256":"90b2b65cb81f6a4f46a3b225b59ecc25704159fc5bae655f1cfbfdcda74921fb","family":"V"},{"source":"H","heading":"v8.3 → v8.4 checklist","index":5,"sha256":"5a6bf3ad75a7d2967ef0200d3c80aa909e152888ba31831bdc78b59271d3c378","family":"Z"},{"source":"H","heading":"v8.2 → v8.3 checklist","index":1,"sha256":"791aebba21961cf340a245d76364cdc014f0d8d8e22890ff4e418cf3385001d8","family":"P"},{"source":"H","heading":"v8.2 → v8.3 checklist","index":2,"sha256":"76f2b4b1623f2d3b6841dabcf7691eb19075c75365cb5603d51d0a2f17ed5ca7","family":"E"},{"source":"H","heading":"v8.2 → v8.3 checklist","index":3,"sha256":"2c5de94ee875834a59a221dbc176dfb0dccc6fce13b59db4c84a8831c4634969","family":"E"},{"source":"H","heading":"v8.2 → v8.3 checklist","index":4,"sha256":"2d33938c6399cc389d7e0b92668d71b630b71f4ca7b777b160c5196098faf73c","family":"Z"},{"source":"H","heading":"v8.2.0 → v8.2.1 checklist","index":1,"sha256":"34602a57e94a077771577db97f386972e8aa623094e3ac95a969a9c74bada4cd","family":"P"},{"source":"H","heading":"v8.2.0 → v8.2.1 checklist","index":2,"sha256":"79258bfc5cf04d045b9e607979322038861d5cd91cbda14280c051b6254cd1a0","family":"E"},{"source":"H","heading":"v8.2.0 → v8.2.1 checklist","index":3,"sha256":"07d409225adca65e07d57aeaad8625e26327b7dd6f6c13fdb01fc54ff2d80ec9","family":"Z"},{"source":"H","heading":"v8.1 → v8.2 checklist","index":1,"sha256":"caf525d23f7f2bc4f1fe58167fa9abc6315288aa9a2fea4218dd841db0660a7c","family":"P"},{"source":"H","heading":"v8.1 → v8.2 checklist","index":2,"sha256":"7302facd0772e426535c49aebb6b8c2f30993b422794d33a65a84619db3fe5a3","family":"B"},{"source":"H","heading":"v8.1 → v8.2 checklist","index":3,"sha256":"c32282381d87448f9f2cd5ed972a11516511934190f4e12c89ecb870345a916d","family":"A"},{"source":"H","heading":"v8.1 → v8.2 checklist","index":4,"sha256":"e93913bca4e110fde518c76b9d36fa55e546238d1381317f5d4ed7028fba6fb3","family":"B"},{"source":"H","heading":"v8.1 → v8.2 checklist","index":5,"sha256":"27943372968f6ff1d971b58c6575ae303ef62ab751805d29dd34e6952354cdec","family":"H"},{"source":"H","heading":"v8.1 → v8.2 checklist","index":6,"sha256":"1d01f0e6450132ba4d6ac86d442e6276f57320bd0f0954e4967e7080c4b80b9d","family":"Z"},{"source":"H","heading":"v8.0 → v8.1 checklist","index":1,"sha256":"3ee84cb3d5e50557b93c44cf132b14c960f3132d8acc3a1a457b99cbedb037be","family":"P"},{"source":"H","heading":"v8.0 → v8.1 checklist","index":2,"sha256":"913c5ece88024ad35a87712ef7c481c0ed65bbe91815cad133fa6cf67bc4bd4a","family":"A"},{"source":"H","heading":"v8.0 → v8.1 checklist","index":3,"sha256":"1d03e8c4472c4b438d4f3d20dc1ec05e6a25e79b3652456f5bc93382ad697e15","family":"B"},{"source":"H","heading":"v8.0 → v8.1 checklist","index":4,"sha256":"4b2cf7ce3a12c86a6404c6f64eed360682dd35576c78757f1050474ea0122412","family":"V"},{"source":"H","heading":"v8.0 → v8.1 checklist","index":5,"sha256":"1a9d8ce891b4de1be1afc57b9fdbdd5aa610463d795fa6c684a4807ac339b4e4","family":"Z"},{"source":"H","heading":"Historical migration shape","index":1,"sha256":"ae6f063cf5f6a95c441ec6bdf31a3dd3b1bdd6c90ecf7c58c36936093ac5d740","family":"S"},{"source":"H","heading":"Historical migration shape","index":2,"sha256":"0f50318765d0bd646260f1661b2a50b6a02ee91b583bae6007af8ac22eb2bf9d","family":"P"},{"source":"H","heading":"Historical migration shape","index":3,"sha256":"b54d2498132bc15c774be256227b1727ff8bb0212eb46b94fbd6e5c20948c430","family":"A"},{"source":"H","heading":"Historical migration shape","index":4,"sha256":"afefbf5cf6a9efa40000fa01465529189a5bb0b4da3f2cdf18b9b00cc6a3cc45","family":"B"},{"source":"H","heading":"Historical migration shape","index":5,"sha256":"3293220094d13d84bab40ba3ea8fc032dbaf93acc218085c304bed18cb12c5e5","family":"B"},{"source":"H","heading":"Historical migration shape","index":6,"sha256":"e58c868c2a5e9915a693289ce4a464123b1b8691af825846614f03765be83720","family":"V"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":1,"sha256":"6366929a529262319913ff40537fa30eef4c4ca21b9beceded3c19af5b94d710","family":"P"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":2,"sha256":"19b6df2f6a71fe2efe04b3fab50a6daea2263a355d6674d9646fe93ddf402dad","family":"P"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":3,"sha256":"618daec0c6acc0b24d48a2a756ddc602da27a775836907aeefd041fc0e09bf9d","family":"B"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":4,"sha256":"38df0c83e51d421b3f2726ce6281ed2346a1ceb6221f60fe3040839abbcd62d4","family":"A"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":5,"sha256":"3f9e6de6224d4fc306a25f91c5418917f4c5c49b413c35407759b9ad9fb74bfa","family":"E"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":6,"sha256":"63afdaac620fd3d4ea4d1d19fadb38065f9962f97bcc6310cd97cb92b2d5bf25","family":"Z"},{"source":"H","heading":"v7.3 → v8.0 checklist","index":7,"sha256":"29134c167e57f59ec0e456363b4065fc69b971e363cc81fd246b185ce805e545","family":"Z"},{"source":"H","heading":"v7.0 → v7.1 checklist","index":1,"sha256":"c1b636147d6f0e5239d3c911ea6610d3f498a4365e7a30bbc9aa87589d87e0cc","family":"I"},{"source":"H","heading":"v7.0 → v7.1 checklist","index":2,"sha256":"357c081500032c3c9827d30aade49ac86709552e35030f49217a441bf9cebd47","family":"I"},{"source":"H","heading":"v7.0 → v7.1 checklist","index":3,"sha256":"564260eb769506ca636fc1439bdbf8ba7d8e99812e98094005bbb6ecb58bfe94","family":"A"},{"source":"H","heading":"v7.0 → v7.1 checklist","index":4,"sha256":"20d4877618e94f0d4249ff624c247776296fd20d6e95851191e8fbcc7a7a5d47","family":"I"},{"source":"H","heading":"v7.0 → v7.1 checklist","index":5,"sha256":"818db68392a7e582687f4442dd293f2643bcf138a362f1de2216212b5e0bc1a9","family":"E"},{"source":"H","heading":"v7.0 → v7.1 checklist","index":6,"sha256":"1c13e1071c75e55dea2f79f1324b8438f73f9351fc27e416896a94ca88ba7e91","family":"Z"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":1,"sha256":"1939c4345fefd3c2ff96fb02d47a9ce181eba0d78339b03f4e195be715163f58","family":"P"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":2,"sha256":"2ee04aca5435fa3be3c5562320073aba39f0ddaf1da598b49f5d3d6eba61da1b","family":"E"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":3,"sha256":"7d1609f8e3555aa93090c37569026153ebae8a6ce524ccd888fdce3b550454e1","family":"E"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":4,"sha256":"f59d2e5d3c219d8ef2cf9d5407fbf359578b35095e333d3c2e832a5bbc29efed","family":"E"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":5,"sha256":"f436733c8678b0f33cdabbbbd66313e6acd5fee479872acc717f10d27e042e72","family":"E"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":6,"sha256":"c0597d71611dc365814471a9a023258f57ffa84f6c3a76d832784787942c4812","family":"V"},{"source":"H","heading":"v7.1 → v7.2 checklist","index":7,"sha256":"f871af7e4e59af4647541fd9af86f080c77f1594a30ee7d22b26406996af309e","family":"Z"},{"source":"H","heading":"v7.2 → v7.3 checklist","index":1,"sha256":"aa7399f5d8c048e063489a8e5cca8e8455c7cbe697f3273c4960b45740df73a3","family":"B"},{"source":"H","heading":"v7.2 → v7.3 checklist","index":2,"sha256":"462c427c019367b4b2371471701f06d7e56ed0e8455c7a45bb1550682c14824b","family":"B"},{"source":"H","heading":"v7.2 → v7.3 checklist","index":3,"sha256":"c5bd75f24a47a8ff27e3cd6335e6d7280c630917d7941bfcd4b82825f57d3e6b","family":"E"},{"source":"H","heading":"v7.2 → v7.3 checklist","index":4,"sha256":"b78bdf5e61676afc9322d8c6172a26b696975c0cf760e231814a33fc9b0b742c","family":"B"},{"source":"H","heading":"v7.2 → v7.3 checklist","index":5,"sha256":"815e50167beaa752dfd6bd1eb0ad7e5160c51417bb50ec0f04a03527cafb112d","family":"Z"},{"source":"H","heading":"v6.1 → v7.0 checklist","index":1,"sha256":"f65b9bd9e16758cf00ddf32c42f84f3e629fcd50598d5ca6d2c67c89e7dc1a10","family":"A"},{"source":"H","heading":"v6.1 → v7.0 checklist","index":2,"sha256":"a8976eab556ab8cf04bff54c7ba397fefb66189af696306a5f277d4bd5eaf5d2","family":"I"},{"source":"H","heading":"v6.1 → v7.0 checklist","index":3,"sha256":"616127e6851998f914e588aba04522498975e78dbd808fe6a10c2482a2e56c7d","family":"A"},{"source":"H","heading":"v6.1 → v7.0 checklist","index":4,"sha256":"ce1f6be2ffc22b6ea42013bc722cddf89b0fc75a7c62cfe0720a498da0cabd30","family":"Z"},{"source":"H","heading":"v6.1 → v7.0 checklist","index":5,"sha256":"75e67dde89ec6efbaf955e85b4982b2857fd1b82cd323bc1d95a20c9bb2d75f6","family":"V"},{"source":"H","heading":"v6.0 → v6.1 checklist","index":1,"sha256":"4d1f17d0c83ede9eb82bfab6de3bba3b12a5f4ffd6c794a3b16145e19df81d58","family":"E"},{"source":"H","heading":"v6.0 → v6.1 checklist","index":2,"sha256":"64a679d4b1852ed29d70d1a1f2a9dfdc385be14978c7a6cd6e2f01b8a9b53256","family":"E"},{"source":"H","heading":"v6.0 → v6.1 checklist","index":3,"sha256":"51381b0349293e0c7deabd43c1518f15fee78dcd3e100a931a66000589aece1a","family":"Z"},{"source":"H","heading":"v5.6 → v6.0 checklist","index":1,"sha256":"819abf9674784419b52f6f80841a50072c98ffc700e103209339c9e8ad96f7b4","family":"E"},{"source":"H","heading":"v5.6 → v6.0 checklist","index":2,"sha256":"e1884f58bb40e7e0745d055ee73f318ed5b71a52695402dd14ae89f21b3d23a8","family":"E"},{"source":"H","heading":"v5.6 → v6.0 checklist","index":3,"sha256":"51381b0349293e0c7deabd43c1518f15fee78dcd3e100a931a66000589aece1a","family":"Z"},{"source":"H","heading":"v5.5 → v5.6 checklist","index":1,"sha256":"9ee11bdc9bacad46929c8e63a4b4a93ab7ae2657f8050b92826c01e99ea9703f","family":"R"},{"source":"H","heading":"v5.5 → v5.6 checklist","index":2,"sha256":"b6f953ceeba00478fa8045bcf29a51ee69ad4b9d0bb229ac461559a5632e890f","family":"H"},{"source":"H","heading":"v5.5 → v5.6 checklist","index":3,"sha256":"08624e55c38aeec53b296f42efaee4c3ad61b5da9d0638599dee66f484d81400","family":"O"},{"source":"H","heading":"v5.5 → v5.6 checklist","index":4,"sha256":"55d359b0f4c819fcc0c4a74f4a61217d061dc429a0827f7e0e7b9c9af18894e4","family":"Z"},{"source":"H","heading":"v5.4 → v5.5 checklist","index":1,"sha256":"f423ce154efeac56eab725a78ba84a6d7218f0abf4aba95f840db35397e5e29d","family":"H"},{"source":"H","heading":"v5.4 → v5.5 checklist","index":2,"sha256":"c229d95ea9277a8eb5ec50259e2957327e4153d51eaed22b422ce782e35d6979","family":"B"},{"source":"H","heading":"v5.4 → v5.5 checklist","index":3,"sha256":"51381b0349293e0c7deabd43c1518f15fee78dcd3e100a931a66000589aece1a","family":"Z"},{"source":"H","heading":"v5.3 → v5.4 checklist","index":1,"sha256":"0d88a91fbb6b8f5108eed27d3fdab821e97f7856631e426d57f93d402c85339e","family":"V"},{"source":"H","heading":"v5.3 → v5.4 checklist","index":2,"sha256":"127731604e5ddbfd2317e98514e572182d47e0b65d7c6e1f475e17833e9ca758","family":"Z"},{"source":"H","heading":"v5.2 → v5.3 checklist","index":1,"sha256":"81dbb69ce8a32e5d3de8a03ff4d261e80bb8e8f2fb36e88f6e191f91f6bb8cc7","family":"B"},{"source":"H","heading":"v5.2 → v5.3 checklist","index":2,"sha256":"6ba0516e665f6e4030e04cd79ce05553dffb51f243936f37234faf1cc87c8f23","family":"B"},{"source":"H","heading":"v5.2 → v5.3 checklist","index":3,"sha256":"d1789ed440ee40292f8c810ae8785c28269bab9f6a2faf0cada14cca22014d22","family":"B"},{"source":"H","heading":"v5.2 → v5.3 checklist","index":4,"sha256":"2d1ae3cd8bd7c1f51534f4d0e41080c47c67fec0ae2df5299e8eb47bb182df14","family":"B"},{"source":"H","heading":"v5.2 → v5.3 checklist","index":5,"sha256":"38ca2ed9da7babe676cec837ced2babbe531ac739ccf00436f44d4a6005f24b8","family":"V"},{"source":"H","heading":"v5.2 → v5.3 checklist","index":6,"sha256":"64bde7301b17026d3a95dae7ca3815c73cdd3c3fefbeb6cd718574d703d78de5","family":"Z"},{"source":"H","heading":"v5.1 → v5.2 checklist","index":1,"sha256":"ba27d430466b3f0cae8b908a3a23a0a639a7c81b439147b418050a4ed2990769","family":"E"},{"source":"H","heading":"v5.1 → v5.2 checklist","index":2,"sha256":"875bec2dfd9d3a5f673ba1fba35175f47cf1099cfb11ec9dd830d9e5e9618460","family":"M"},{"source":"H","heading":"v5.1 → v5.2 checklist","index":3,"sha256":"d582548149e0277246b78d9c4af45769e3b9a456ffc1fd7cf9098d63c3137edb","family":"M"},{"source":"H","heading":"v5.1 → v5.2 checklist","index":4,"sha256":"8e3bac6613490b421762ae63bbfb7359e9137d2503404d060aad13ea0ce57666","family":"V"},{"source":"H","heading":"v5.1 → v5.2 checklist","index":5,"sha256":"06b3e983fa5ba7c35ece88fa7216686ee786487889d001e71a0a090bbf9c7587","family":"B"},{"source":"H","heading":"v5.1 → v5.2 checklist","index":6,"sha256":"64bde7301b17026d3a95dae7ca3815c73cdd3c3fefbeb6cd718574d703d78de5","family":"Z"},{"source":"H","heading":"v5.0 → v5.1 checklist","index":1,"sha256":"1fde358a8f95ec68d061e2373eac8badc30765551986f9c39d2b23c1aec67b9f","family":"O"},{"source":"H","heading":"v5.0 → v5.1 checklist","index":2,"sha256":"3253ab6c322a31fcd3926a70f2b28b828e7f7be6daa04400f0c1e4a383626d12","family":"B"},{"source":"H","heading":"v5.0 → v5.1 checklist","index":3,"sha256":"edc093660ae22cc1348e1dbd85c52a366396eda89f96f6e453ce8c959e8d78cf","family":"O"},{"source":"H","heading":"v5.0 → v5.1 checklist","index":4,"sha256":"a66ac6e74d5f436f21e168352baa8b608131398c894b21decbe7451b3b9bc33a","family":"O"},{"source":"H","heading":"v5.0 → v5.1 checklist","index":5,"sha256":"62c316eb19f46754a47b74d38b6100a7489944161cfce61f6285d8522f529a6d","family":"B"},{"source":"H","heading":"v5.0 → v5.1 checklist","index":6,"sha256":"1cdf994d74dc6aa625a3a249b57a9f968d9bb3986768b0fae241ec4c12e86268","family":"Z"},{"source":"H","heading":"v4.4 → v5.0 checklist","index":1,"sha256":"a3b932b72def28e7a4854b5ce1042914f35c96af41442030c3e84b04fea092e5","family":"E"},{"source":"H","heading":"v4.4 → v5.0 checklist","index":2,"sha256":"33fc2f851b887200f49814b52bcf5cc032935882ad7efb1e7c08b6e91d8f6e49","family":"V"},{"source":"H","heading":"v4.4 → v5.0 checklist","index":3,"sha256":"edb23312765153d14b08ff72be58965f7df8fb3ae1da08d2ca895f0e23cc3666","family":"Z"},{"source":"H","heading":"v4.3 → v4.4 checklist","index":1,"sha256":"1831083d2ca0b23fb95d411a3161c92246eb41131e0f5cc9be223709e561374f","family":"A"},{"source":"H","heading":"v4.3 → v4.4 checklist","index":2,"sha256":"127731604e5ddbfd2317e98514e572182d47e0b65d7c6e1f475e17833e9ca758","family":"Z"},{"source":"H","heading":"v4.2 → v4.3 checklist","index":1,"sha256":"afc591645cb9e1006056ce8c6cca6efa63ed5afeca3452432b877e1dda52c046","family":"E"},{"source":"H","heading":"v4.2 → v4.3 checklist","index":2,"sha256":"71fc39a5e6c0a84c048cc5e77ef09de3f242a5226e79bdb02d09113552221333","family":"E"},{"source":"H","heading":"v4.2 → v4.3 checklist","index":3,"sha256":"51381b0349293e0c7deabd43c1518f15fee78dcd3e100a931a66000589aece1a","family":"Z"},{"source":"H","heading":"v4.1 → v4.2 checklist","index":1,"sha256":"3da5e8d951d77729dc9bc133c0cf1f2e74874e2dcb8d90fdbdd09834837ed879","family":"E"},{"source":"H","heading":"v4.1 → v4.2 checklist","index":2,"sha256":"127731604e5ddbfd2317e98514e572182d47e0b65d7c6e1f475e17833e9ca758","family":"Z"},{"source":"H","heading":"v4.0 → v4.1 checklist","index":1,"sha256":"0ee8c28ebb604e57834d8c9707f9cceda39fe13d0f29e13b45e696402abf6b24","family":"I"},{"source":"H","heading":"v4.0 → v4.1 checklist","index":2,"sha256":"e08a4eb6c58ae782f3ea920f0b4c037551aee5c94822f793919b0be528321b23","family":"O"},{"source":"H","heading":"v4.0 → v4.1 checklist","index":3,"sha256":"51381b0349293e0c7deabd43c1518f15fee78dcd3e100a931a66000589aece1a","family":"Z"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":1,"sha256":"e9b4da4b35e2d18f7635865ab7dfcc75e8f09e36d762337618ca96b15eccd275","family":"B"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":2,"sha256":"82e9ba88456e528e7e14349f26b7a3cd93a3d20c5a7d112c481e74fefbf0d55c","family":"B"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":3,"sha256":"e295722fee0beaa3ee5ba1977eb89445a0efa25d8fd18ef5b42f5394ddb7d4e9","family":"O"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":4,"sha256":"418c4eded34fd3c659368384d2d915162d799dc1d8f0377977b613345863675c","family":"A"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":5,"sha256":"536ce81ab19852f99f5f461ad21330b67e8c7b623059831ff8864ce89bc6b6ec","family":"M"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":6,"sha256":"965155ad785f152bd49a52061ad8d7dfb3e56cda59ac43b61e1bb1522896bd8d","family":"V"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":7,"sha256":"fab7d47a6a40d7e5f93c3f04c53d9d8596855133c7c6cedb5e5ae16787b2cdc2","family":"O"},{"source":"H","heading":"v3.4 → v4.0 checklist","index":8,"sha256":"b8a3ca31d8eeb4dd16564e8e17f82669795ac3626e603c40e36d161dad712130","family":"Z"},{"source":"H","heading":"v3.3 → v3.4 checklist","index":1,"sha256":"2ad383b469e942edbe80571be6edb127640fe6d6fb697cfac497a3c42e8fc6b4","family":"A"},{"source":"H","heading":"v3.3 → v3.4 checklist","index":2,"sha256":"dc907d4e33f334b1fe67e34a345c1fb665fe9a524541e25221c3a43f7ce81701","family":"O"},{"source":"H","heading":"v3.3 → v3.4 checklist","index":3,"sha256":"b4599370c706b775dc5729f802fb39b070f35bc14bc3442f96ede0ed23e18c82","family":"V"},{"source":"H","heading":"v3.3 → v3.4 checklist","index":4,"sha256":"e2052e99e139f1e7f3024fcf636b7f9439398d71255fcd78ecb93c8cf6e90e27","family":"Z"},{"source":"H","heading":"v3.2 → v3.3 checklist","index":1,"sha256":"8323be24b6510135fa5230f07a965cf328216b34df08436aa0551773cd844c08","family":"M"},{"source":"H","heading":"v3.2 → v3.3 checklist","index":2,"sha256":"68cca94d24ae8a10f5a45fca433b798f4e8be1a1b7498188c202b7e5ace58411","family":"R"},{"source":"H","heading":"v3.2 → v3.3 checklist","index":3,"sha256":"27b8658f23ca6410503244bfb6c245c4df6a22e98b2099eb3747f26c1e306a91","family":"Z"},{"source":"H","heading":"v3.0 → v3.1 checklist","index":1,"sha256":"74e095fa6200dbbe53cf9a1385c695c3eea92cf5b2826881f4e50137e4d8b92c","family":"B"},{"source":"H","heading":"v3.0 → v3.1 checklist","index":2,"sha256":"3472883a10624ab57d3a8cea6a98256651c8e7f4e0b4f2b4a5ece755c7999f52","family":"E"},{"source":"H","heading":"v3.0 → v3.1 checklist","index":3,"sha256":"2ab7a3163e15ebc04e3f3a11d9ca6d0d0b2f364b54ded03bf648332b4b6a0d2a","family":"E"},{"source":"H","heading":"v3.0 → v3.1 checklist","index":4,"sha256":"93feb6ba6749e0f8c32d7e03632c9d3c4b9e9b09f8a9d063e26cabe2c70fcdd1","family":"B"},{"source":"H","heading":"v3.0 → v3.1 checklist","index":5,"sha256":"c99a0b7526241c5a45fe7a1ba73b53d4bb580a75bb8823b6ad0c6e4c5bd0a186","family":"E"},{"source":"H","heading":"v3.0 → v3.1 checklist","index":6,"sha256":"33f20ecd725484a4947d4d67ca8ab82ccbe284d4c1678c34cda30223da9d9876","family":"Z"},{"source":"H","heading":"Artifact renames","index":1,"sha256":"76ea35db064aada38589f7e90c7dfae82ab567c56ca9ab86f1488d3da3e75359","family":"S"},{"source":"H","heading":"Artifact renames","index":2,"sha256":"56c5a4587211be596458b44b20646304bf788a0f05a8283be4c2c92972e20b86","family":"S"},{"source":"H","heading":"Artifact renames","index":3,"sha256":"72da3aaab8e4d9fa9bef25159d2ae2fffb338141583c887e707103fc3c6d80bb","family":"P"},{"source":"H","heading":"Artifact renames","index":4,"sha256":"ac26f6a2f4dfb8d591e45fc5a06de28514bcde6e98ff220b52720c857c6dca95","family":"Z"},{"source":"H","heading":"Historical structural conformance","index":1,"sha256":"593ad7504e1692a0a86971af01fa3bffdf5d9bd69ad41a360139532906144190","family":"S"},{"source":"H","heading":"Historical structural conformance","index":2,"sha256":"89edd90550deb2801d847b00586978513e87f4e05bbbb78fb94dc5b74f0afadb","family":"A"},{"source":"H","heading":"Historical structural conformance","index":3,"sha256":"918902142715aeb087ab16190960f4ccfb37af5cb38073995698bb5598f6c760","family":"A"},{"source":"H","heading":"Historical structural conformance","index":4,"sha256":"f74f41dbff3d8d8a5b1ca3e0531de3cdefda9f4208805716e8cf166adef66c6e","family":"B"},{"source":"H","heading":"Historical citations","index":1,"sha256":"97e2da6d020d9e8287045157dff9a2421abfdd2d46c10a30e13db112c91c9e32","family":"B"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":1,"sha256":"9604a9f44800db9fc8b2107bbcdc7a65fc35ba68e9dc7d52fe305667c00a5eb9","family":"B"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":2,"sha256":"f4c8a043b415b79777da44e793a334be061e621a85c98dc9d00a381a19dcdce9","family":"E"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":3,"sha256":"be72557b1db17a2db9f2fb98e04082db6f0cdd006a099ad0a013a4b91cc6bc85","family":"B"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":4,"sha256":"006968d69c7ca8d7130dc22983f8dce661f56c91d3794af4777a201befaecd73","family":"V"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":5,"sha256":"5640bd76e0ff24bddcf2367860a40cc1f758a3a3507a505667292dd8673d81f6","family":"B"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":6,"sha256":"004aac75fcf8094736a1904d49222e3a251902c3ccc18351f2e5ffb4a84688d3","family":"M"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":7,"sha256":"78e8729206b3dc5663366dfae3a1ab86f869f612003cb27a63224f171755511c","family":"E"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":8,"sha256":"244602b26f139ae2de0e1436221813b3897e1a0bde2b58e408f8bdac2be77b7a","family":"M"},{"source":"H","heading":"v2.1 → v3.0 checklist","index":9,"sha256":"eb4b6b48756194e78746512e464c80472a08da3be4b9376b0798524379c354db","family":"Z"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":1,"sha256":"df06592c2ccbcf465dc0092499fad205343f76d006ee615ae07838d7d122079c","family":"A"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":2,"sha256":"464440da6ea74743eba0b1d4022da01621463657ddd8b698b7c95e3f22738b15","family":"B"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":3,"sha256":"313c3c9c6e865f133a10c29f3eaa642c51b83cf89d9a3a1907af0dcefcacd760","family":"B"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":4,"sha256":"a1d603adbe10603128351c1498e95693b089544ba92935c48f32dad6a363ac5b","family":"B"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":5,"sha256":"b17147b1adee2450c7cde642091d01f7da57ae797ee04569e38b158edc8c5c86","family":"O"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":6,"sha256":"7f415f804c06a6cd371b4dd887df311bd38b8f456097aa7ebd0be8a6836c3592","family":"Q"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":7,"sha256":"f0c9db0520681c94fa388fa9f5ec5233b5642d3685c56f8217f177c85d312b11","family":"M"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":8,"sha256":"596dc09090b5835e1af0dd2f917d26310878e4967ce19148ca71fe84e1f44854","family":"V"},{"source":"H","heading":"v2.0 → v2.1.0 checklist","index":9,"sha256":"daf467921f1c09e6989165dd7050ed74198711e244e7b0a2ce9cc0ae2e78f687","family":"Z"}]}')
ORDER = 'I P S A R B M E J H N Q W O V Z'.split()
ADAPTER_PINS = {'schema.py': '6e7c3d3de8ca67089f0a5f395ebb14bb00e581fadaf4d1e9272707666a0d4809', 'step_pre3_to_3.py': 'b08e63d7182d5a51d30a1973ba3f098448a174e208e9739783688d7ca82ab4b3', 'step_3_to_4.py': 'effc084a74cb31c1aea0983e89bc94e0a08a3bd26137ec87ae9fc94b9c2846f5', 'step_4_to_5.py': 'ae4dcf1ee639aa556fccf4ddbc1b70229b942d84e6a365c12009023af717501b'}
ARCHIVE_PREFIX = {'bytes': 62876, 'sha256': 'f6b5755d87928e835e22af8d52c546c5ffe9b42c540e3d0eebcc41df3db6333e'}

GUIDE_SNAPSHOT = bytes.fromhex('3c612069643d227638342d2d7639302d636865636b6c697374223e3c2f613e0a23232076382e3420e286922076392e3020636865636b6c6973740a0a54686973206d616a6f722072656c65617365207265706c61636573207468652052554e20616e6420504c414e2067756964657320776974682063617264732c206b657973206d6967726174696f6e206f6e2074686520626f6172640a736368656d6120616e6420726574697265732074686520382e7820616374696f6e2d6e616d6520616c69617365732e20496e7374616c6c696e6720392e30206d69677261746573206e6f7468696e6720627920697473656c662e20392e302072756e73206f6e6c790a7468652063757272656e74206c61796f757420616e642072656675736573206120776f726b7370616365207468617420686173206e6f74206265656e206d696772617465640a285b666f7277617264206f6e6c795d2823666f72776172642d6f6e6c7929292e0a0a312e204265666f7265207570646174696e672074686520696e7374616c6c2c206d6f766520616e792066696c6520796f7520616464656420756e64657220607265666572656e6365732f617263686574797065732f6020746f0a202020602e7461636b6c652f617263686574797065732f60206f7220607e2f2e7461636b6c652f617263686574797065732f602e2054686520696e7374616c6c206e6f206c6f6e67657220636172726965730a20202073656c662d646576656c6f706d656e7420617263686574797065732c20616e6420616e207570646174652064726f70732066696c6573206c6566742074686572652e0a322e204d6967726174652074686520626f617264207468726f75676820746865205b736368656d612d6b65796564206d6967726174696f6e5d2823736368656d612d6b657965642d6d6967726174696f6e2920616e64206974730a2020205b73746570735d28236d6967726174696f6e2d73746570732920746f206275636b6574206035602e204120626f6172642077686f73652066656e636564206578616d706c65206e6576657220636c6f73657320697320726566757365643b0a202020636c6f7365207468652066656e636520616e642072756e20746865207374657020616761696e2e204120466f637573656420776f726b737061636520686173206e6f20626f6172643a2072656e616d6520606c6f672e6d64602c0a202020606c6f672d617263686976652e6d646020616e64206075736167652e6d646020746f2060686973746f72792e6d64602c2060686973746f72792d617263686976652e6d646020616e6420607265736f757263652d75736167652e6d64602e0a332e2052756e20726f77732031e280933136206f6e20746865206d6967726174656420636f70792e20526f7720313220636865636b73206f6e6c792074686520627269656673206f66207461736b73207468617420617265206e6f740a202020636c6f7365642028436f6d706c6574652c20536b6970706564206f7220556e76657269666961626c65292c20616e64207265706f72747320604566666f727420776974686f7574205469657220726561736f6e6020666f7220737563680a202020612062726965662077686f7365204566666f7274206973206e6f7420606c6f776020616e64207468617420686173206e6f205469657220616e64206e6f205469657220726561736f6e2e0a202020546869732069732065787065637465643a20616464206120602a2a5469657220726561736f6e2a2a60206c696e6520746f207468617420627269656620736179696e672077687920697473204566666f727420646570617274730a20202066726f6d207468652064656661756c742c20617320746865205b7461736b2074656d706c6174655d282e2e2f7461736b2e746d706c2e6d64292073686f77732e20496e207468652073616d65206f70656e206272696566732c2072656e616d6520602a2a546f75636865732a2a6020746f0a202020602a2a57726974652073636f70652a2a6020616e642060446f6e652d7369676e616c6020746f2060416363657074616e636520636865636b602c20616e64207265706c61636520616e2060696e686572697460204566666f727420776974680a20202061206c6576656c2e0a342e205265706c616365207265746972656420382e7820616374696f6e206e616d657320696e20666f72776172642d6c6f6f6b696e672070726f6d7074732077697468207468652063757272656e74207265717565737420776f7264733b0a2020205b7465726d696e6f6c6f67792e6d645d282e2e2f7465726d696e6f6c6f67792e6d6429206d6170732065616368206f6c64206e616d652e20507265736572766520686973746f726963616c207265636f72647320766572626174696d2e0a352e2050726f66696c6573206e656564206e6f20616374696f6e3a20616e20656e74727920776974686f757420616e206964207374617973207265616461626c652c20616e6420746865206e65787420726574726f20746861740a202020746f75636865732069742061737369676e7320616e20696420616e6420636f6d70757465732069747320636f6e666964656e63652e0a362e2054686520726f7574696e67206669656c647320286054696572602c20605469657220726561736f6e602c2060457363616c6174696f6e602920617265206f7074696f6e616c3b206120627269656620776974686f7574207468656d0a2020206b65657073207468652064656661756c742e20506c616e6e696e672072756e73206f6e2061206d6f72652063617061626c652074696572207468616e20746865204578656375746f722773207768656e65766572207468650a2020206d6f64656c206d61702062696e6473206d6f7265207468616e206f6e6520746965722e0a372e205265636f7264207468652070617468206d617070696e672077697468207468652061646f7074696f6e2e0a0a3c612069643d227639322d2d7639332d636865636b6c697374223e3c2f613e0a23232076392e3220e286922076392e3320636865636b6c6973740a0a416e2061637469766520392e3220776f726b73706163652061646f70747320392e332e302077697468207468697320636865636b6c6973742e20546869732072656c65617365206368616e6765732074686520706c616e207669657727732074656d706c61746520616e640a746865207374796c696e67206f6620617578696c696172792070616765732c20616e64206974206368616e676573206e6f2066696c6520666f726d61742e0a0a312e2049662074686520776f726b737061636520686173206120706c616e20766965772c2072656275696c6420697420756e64657220697473207374616e64696e67207669657720726571756573742c2073696e6365207468652074656d706c617465206368616e6765642e0a202020576974686f7574207468617420726571756573742c206275696c64206e6f20766965772e204578697374696e6720617578696c69617279207061676573206368616e6765206f6e6c79206f6e20726571756573743b206d6f7665206f6e6520746f207468650a202020706c616e207669657727732062617365206f6e6c79207768656e20746865206f776e65722061736b732e0a322e205369626c696e6720776f726b73706163657320617265206f7074696f6e616c2e204120776f726b73706163652074686174206465636c61726573206e6f6e65206e65656473206e6f206368616e67652e0a0a3c612069643d227639332d2d763130302d636865636b6c697374223e3c2f613e0a23232076392e3320e28692207631302e3020636865636b6c6973740a0a416e2061637469766520392e3320776f726b73706163652061646f7074732031302e302e302077697468207468697320636865636b6c6973742e20546869732072656c656173652073686970732065766572792070726f6772616d20617320612073637269707420756e6465720a60736372697074732f602028507974686f6e20332e3130206f72206c61746572292c20616e64206974206368616e676573206e6f2066696c6520666f726d61742e0a0a312e20416e206f776e65722077686f2072756e73206120392e33206c6f6f706261636b206c6976652070726f64756365722073746f7073206974206265666f7265207570646174696e673b2031302e30207265746972657320746865206c697665207669657720616e640a2020207368697073206e6f2070726f64756365722e0a322e2049662074686520776f726b737061636520686173206120706c616e20766965772c2072656275696c6420697420776974682060736372697074732f706c616e5f766965772e70796020756e64657220697473207374616e64696e67207669657720726571756573742c0a202020617320746865205b706c616e20766965772067756964655d28706c616e2d766965772e6d6429207374617465732e20576974686f7574207468617420726571756573742c206275696c64206e6f20766965772e0a332e20536176656420636f70696573206f6620392e78207265636970652070726f6772616d7320617265206f62736f6c6574653b2075736520746865207363726970747320756e6465722060736372697074732f6020696e20746865697220706c6163652e0a342e204120766572696669636174696f6e207265636f7264207468617420616e20696e7374616c6c65642060636170747572652e707960206f7220606c696e745f72756e6e65722e707960206d616465207768696c652072756e6e696e672066726f6d206f7574736964652074686520776f726b696e670a2020206469726563746f7279206e616d65732074686174207363726970742773207368613235362c20736f2069742069732072656675736564206f6e63652074686520696e7374616c6c207570646174657320746865207363726970742e20526572756e2074686f73650a202020636865636b7320756e64657220746865207570646174656420696e7374616c6c2e0a352e205b53797374656d204f6e655d2873797374656d2d6f6e652e6d642920676f6573207468726f7567682074686520686f73742773206074797065736166652d61696020736b696c6c2e2041207265636f72646564206053797374656d204f6e6520636f6e73656e743a60206c696e65206b65657073206974730a2020206d65616e696e6720616e64206e65656473206e6f206368616e67653b206e6576657220636f7079206f6e652066726f6d206120706172656e74206f72206e65696768626f72696e6720776f726b73706163652e0a0a3c612069643d22763130302d2d763130312d636865636b6c697374223e3c2f613e0a2323207631302e3020e28692207631302e3120636865636b6c6973740a0a416e206163746976652031302e3020776f726b73706163652061646f7074732031302e312e302077697468207468697320636865636b6c6973742e0a0a312e204164642060476174653a2046756c6c60206f6e206c696e652033206f6620616e2061637469766520436f6f7264696e6174656420706c616e2c20666f6c6c6f77696e672060706c616e2e746d706c2e6d64603b206b65657020697473207469746c65206f6e206c696e65203120616e64206b6565702061204c69746520706c616ee28099732060476174653a204c69746560206f6e206c696e6520312e0a322e20557365207468652060686973746f72792e746d706c2e6d6460206a6f75726e616c20666f726d2060636f7272656374696f6e206379636c65204e206f6620333a203c6661696c7572653e20e28692203c636f7272656374696f6e3e3b203c76616c69646174696f6e20636f6d6d616e643e3a203c726573756c743e6020666f72206e657720636f7272656374696f6e207265636f7264733b207072657365727665206f6c6465722060617474656d7074204e3a60207265636f7264732e0a332e205772697465206c6966656379636c65206041746020636c6f636b732077697468207365636f6e64732c2060595959592d4d4d2d44445448483a4d4d3a53535b2e6666665d285a7cc2b148483a4d4d29602c20617320607265736f757263652d75736167652e746d706c2e6d6460207374617465733b206d696e7574652d6f6e6c7920616e642073706163652d73657061726174656420636c6f636b732072656d61696e20756e6d656173757265642e0a342e20557365207468652073616d65206041746020636c6f636b20666f726d617420696e20746865206c656467657220626f6479206f6620606c6974652d706c616e2e746d706c2e6d64603b206b65657020616e20756e6f6273657276656420636c6f636b20617320606e2f61602e0a352e205573652074686520757064617465642060726574726f2e746d706c2e6d646020726563697065733a20417474656d707473206163636570747320626f7468206a6f75726e616c20666f726d733b204761746520616363757261637920636f756e74732064697374696e63742073657373696f6e73206f76657220746865206172636869766520616e642063757272656e7420686973746f727920616e64207265706f72747320756e64617465642068656164696e67733b20426c6f636b6564206475726174696f6e73206578636c7564657320537461746520736e617073686f74206c696e65732e0a362e20457870656374206c696e7420726f77203133205741524e206c696e657320666f7220646174656420656e747269657320616674657220746865206e657765737420537461746520736e617073686f7420616e6420666f7220756e64617465642073657373696f6e2068656164696e67733b207468657365207761726e696e677320646f206e6f74206265636f6d65206d616e6461746f7279206661696c757265732e0a372e204275696c6420616e206f7074696f6e616c20602d2d696e6974696174697665602070616765206f6e6c7920756e64657220616e206f776e657220726571756573742c20666f6c6c6f77696e6720746865205b706c616e20766965772067756964655d28706c616e2d766965772e6d6423696e69746961746976652d76696577293b2069742072656164732074686520726f6f7420616e64206f6e6520686f70206f66206465636c61726564207369626c696e6720776f726b7370616365732e0a382e204e616d6520666f7262696464656e20616374696f6e20636c617373657320696e206e6577207461736b206272696566732077697468207468652060466f7262696464656e20616374696f6e7360206669656c64206f6620607461736b2e746d706c2e6d64602c20666f6c6c6f77696e6720746865205b64657369676e2067756964652773206272696566206f626c69676174696f6e735d2864657369676e2d616e642d636f6e74726163742e6d64293b206578697374696e6720627269656673206e656564206e6f206368616e67652e0a392e204b656570207468652063757272656e7420776f726b737061636520736368656d6120616e642066696c6520666f726d6174733b20746869732072656c65617365206368616e676573206e6569746865722c20616e6420616e206578697374696e67207265636f726465642053797374656d204f6e6520636f6e73656e74206b6565707320697473206d65616e696e672e0a0a3c612069643d22763130312d2d763130322d636865636b6c697374223e3c2f613e0a2323207631302e3120e28692207631302e3220636865636b6c6973740a0a416e206163746976652031302e3120776f726b73706163652061646f7074732031302e322e302077697468207468697320636865636b6c6973742e204974206b6565707320607461636b6c652d776f726b73706163652f356020616e642061646473206e6f207265717569726564206669656c642e0a0a312e20576f726b206f6e206120646973706f7361626c6520636f70792c206173205b41646f7074696e6720612072656c656173655d282361646f7074696e672d612d72656c6561736529207374617465733b206c6561766520746865206f726967696e616c20756e6368616e67656420756e74696c206c696e7420706173736573206f6e2074686520636f70792e0a322e20466f7220657665727920436f6d706c657465207461736b206f6e2074686520626f6172642c2068617368206974732062726965662077697468206073686132353673756d203c62726965663e602c206f72206073686173756d202d6120323536203c62726965663e6020776974686f7574206073686132353673756d602e0a332e2050757420602a2a4272696566207368613235362a2a3a203c3634206c6f7765726361736520686578206469676974733e60206f6e20697473206f776e206c696e6520696e20746865207461736b2773207265706f72742c206f75747369646520636f64652066656e6365732e20506c616365206974207269676874206265666f726520746865207265706f72742773206046696e616c207374617475733a60206c696e652c206f72207269676874206265666f72652069747320602a2a52656d61696e732a2a3a60206c696e65207768656e20697420686173206e6f6e652e205468656e20617070656e64206042726965662073686132353620542d4e4e3a203c7468652073616d6520686173683e60206f6e20697473206f776e206c696e652c206f75747369646520636f64652066656e6365732c20746f2074686520656e64206f662060686973746f72792e6d64602e20486973746f7279206f6e6c792067726f77733a206e65766572206564697420616e206f6c64657220656e7472792e2054686174207265706f7274206c696e6520616e642074686520686973746f7279206c696e652061726520746865206f6e6c79206368616e6765732061646f7074696f6e206d616b657320746f206120636c6f736564207461736b2773207265636f7264732e20446f20626f7468206265666f726520616e79206f74686572206564697420746f206120636c6f7365642062726965662e20536b697070656420616e6420556e76657269666961626c65207265706f727473206d617920636172727920626f746820746f6f2e0a342e204166746572207374657020332c206120636c6f736564206272696566206368616e676573206f6e6c79206279206572726174756d2e20416e20616374697665206465636973696f6e20617574686f72697a65732074686520656469743b207468656e20617070656e6420602a2a4272696566206572726174756d2a2a3a20442d4e4e20c2b720736861323536203c686173682061667465722074686520656469743e6020746f20697473207265706f72742e0a352e20476976652065616368206f70656e206272696566206f6e65206c696e6520696e20507572706f736520616e642073636f70652c20602d202a2a44657461696c2a2a3a2066756c6c60206f7220602d202a2a44657461696c2a2a3a20696e74657266616365602e20557365206066756c6c6020666f7220746865205b6e65787420776176655d287665726966792e6d64236d696c6573746f6e652d72656164696e6573732920616e6420666f7220616e792062726965662077686f736520726f7720697320526561647920746f2072756e2c20496e2070726f6772657373206f7220436865636b696e672e205573652060696e746572666163656020666f722074686520726573742e20526f77203138206661696c73206120526561647920746f2072756e20726f772074686174206e616d657320616e20696e746572666163652062726965662e204564697420746865206272696566206f6620616e20496e2070726f6772657373206f7220436865636b696e67207461736b206f6e6c792061742074686174207461736b277320626f756e646172792c206e6576657220647572696e6720616e20617474656d70742e0a362e2047697665206120627269656620796f7520726169736520746f206066756c6c60207468652073796d626f6c206c6564676572206f6620607461736b2e746d706c2e6d64602e20556e64657220496e7465726661636520616e6420696e76617269616e74732c20602a2a50726f64756365732a2a6020616e6420602a2a436f6e73756d65732a2a60206561636820686f6c6420606e6f6e6560206f7220696e64656e746564207375622d6974656d732e20457665727920636f6e73756d6564206e616d652067657473206f6e6520736f757263653a206066726f6d20542d4e4e602c206066726f6d20542d4e4e205b7369626c696e675d60206f72206065786973747360207769746820616e20616e63686f726564206369746174696f6e2e2041206066726f6d20542d4e4e60207461736b206d75737420626520616e20616e636573746f72207468726f7567682060446570656e6473206f6e602e204120605b7369626c696e675d6020736f75726365206d75737420616c736f2061707065617220696e207468652062726965662773206f776e2060446570656e6473206f6e602063656c6c2e2041206e616d6520686173206f6e652070726f647563696e672062726965663b20726f77203138206661696c732061206e616d6520746861742074776f206272696566732070726f647563652e20546865207461736b2d626f756e646172792072756c65206f6620737465702035206170706c696573206865726520746f6f2e20416e20696e74657266616365206272696566206e65656473206e6f206c65646765722e0a372e2041646420602a2a4f776e65722a2a3a20542d4e4e20c2b7202a2a436c61757365732a2a3a20432d78786020616674657220602a2a537570657273656465732a2a60206f6e6c79206f6e2061206465636973696f6e20796f752077616e7420636865636b65643b206569746865722070617274206d6179206265206f6d69747465642e20546865206f776e65722773206272696566206d757374206369746520746865206465636973696f6e20696420616e642c206174206066756c6c602064657461696c2c2063617272792065616368206e616d656420636c6175736520636f6d70696c65642e205768656e2061206465636973696f6e2077697468207468657365206c696e6573207375706572736564657320616e206561726c696572206f6e652c20746865206561726c6965722068656164696e67206e616d65732069742c2061732060e2a4b4207375706572736564656420627920442d4e4e602e20526f77203139206661696c7320612068656164696e672074686174206e616d657320616e6f746865722c20616e642061207374696c6c2d616374697665207072656465636573736f72206973206e6f2066696e64696e672e0a382e2052756e2060736372697074732f6c696e742e7079203c736c75673e60206f6e2074686520636f707920616e6420657870656374203139206f6620313920726f77732073696c656e742e2052657061697220612066696e64696e672066726f6d20616e6f7468657220726f7720617320697473206f776e206775696465207374617465732c20616e64206120636c6f736564206272696566206f6e6c79206279206572726174756d2e0a392e204120776f726b737061636520746861742061646f707473206e6f7468696e67206b6565707320776f726b696e672e20526f777320313820616e6420313920736b6970206c65676163792062726965667320616e64206465636973696f6e732c20616e6420726f772031342061736b7320666f72207468652068617368206f6e6c79206166746572207468652031302e322e30207374616d702e20526f772032207265706f727473206120646570656e64656e6379206f6e206120536b6970706564207461736b20616e64206120726571756972656d656e742077686f73652074726163696e67207461736b732061726520616c6c20536b69707065642e205265706169722074686520666972737420627920646570656e64696e67206f6e2074686520737563636573736f722c20616e6420746865207365636f6e64206279206e616d696e672074686520536b6970706564207461736b206f6e20616e206f70656e20737563636573736f72277320602a2a4c696e656167652a2a3a60206c696e652e0a31302e204120766572696669636174696f6e20726f756e64206d6179206b656570206066696e64696e67732e6d64602c2063617070656420617420746872656520726f756e647320756e6c65737320604147454e54532e6d64602073657473206056657269667920726f756e64206361703a204e602e20416e2060416363657074616e63652076616c696461746f723a60206c696e6520696e20604147454e54532e6d6460206e656564732061206465636973696f6e207265636f7264696e6720746865206f776e6572277320726571756573742e204e656974686572206e656564732061206d6967726174696f6e20737465702e0a31312e204c6173742c207365742074686520602a2a4d6574686f646f6c6f67793a205461636b6c652031302e322e302a2a60207374616d7020696e2074686520776f726b737061636520604147454e54532e6d64602c206f6e6c792061667465722073746570203320636f7665727320657665727920436f6d706c657465207461736b2e205468656e2072756e2060736372697074732f6c696e742e7079203c736c75673e6020616761696e20616e6420657870656374203139206f6620313920726f77732073696c656e742e2046726f6d206e6f77206f6e20726f772031342072657175697265732074686174206c696e6520696e206561636820436f6d706c657465207265706f72742e0a0a3c612069643d22736368656d612d6b657965642d6d6967726174696f6e223e3c2f613e0a')

def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    """Independent no-follow physical oracle, including modes and empty directories."""
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(parent) / name
            entry = path.lstat()
            relative = path.relative_to(root).as_posix()
            if stat.S_ISLNK(entry.st_mode):
                result[relative] = {'type': 'symlink', 'mode': stat.S_IMODE(entry.st_mode),
                                    'sha256': None, 'target': os.readlink(path)}
            elif stat.S_ISDIR(entry.st_mode):
                result[relative] = {'type': 'directory', 'mode': stat.S_IMODE(entry.st_mode), 'sha256': None}
            elif stat.S_ISREG(entry.st_mode):
                result[relative] = {'type': 'file', 'mode': stat.S_IMODE(entry.st_mode),
                                    'sha256': digest(path.read_bytes())}
            else:
                raise AssertionError('unsupported fixture object: ' + relative)
    return dict(sorted(result.items()))


def tree_sha(root):
    return digest(canonical(inventory(root)))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def read_json(path):
    return json.loads(path.read_bytes())


def source_id(item):
    return json.dumps([item['source'], item['heading'], item['index']], ensure_ascii=False, separators=(',', ':'))


PURE = r'''
import importlib.util,json,sys,os
from pathlib import Path
install,input_file,output_file,forbidden=map(Path,sys.argv[1:5])
reads=[]
def audit(event,args):
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        value=os.path.abspath(os.fsdecode(args[0]));reads.append([event,value])
        if value==str(forbidden) or value.startswith(str(forbidden)+os.sep):
            raise AssertionError('installed consumer opened repository history/source: '+value)
sys.addaudithook(audit)
sys.path.insert(0,str(install/'scripts/migrate'))
spec=importlib.util.spec_from_file_location('compact_fixture',install/'scripts/migrate/compact.py')
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
data=json.loads(input_file.read_bytes())
files={k:bytes.fromhex(v) for k,v in data['files'].items()}
import schema
for name in ('step_pre3_to_3','step_3_to_4','step_4_to_5'):
    step=__import__(name)
    assert step.schema_of is schema.schema_of
before_files=dict(files);before_data=json.dumps(data,sort_keys=True)
result=module.diagnose(files,data['context'],data['catalog'])
assert files==before_files and json.dumps(data,sort_keys=True)==before_data
output_file.write_text(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n')
output_file.with_suffix('.reads.json').write_text(json.dumps(reads))
'''

INTERRUPT = r'''
import json,os,runpy,sys
from pathlib import Path
module_path,operation,job,count,mode,signal_file=sys.argv[1:]
state=json.loads((Path(job)/'state.json').read_bytes());source=state['source']
real=os.rename;seen=0
def rename(*args,**kwargs):
    global seen
    if str(args[0])!=source and str(args[1])!=source:return real(*args,**kwargs)
    seen+=1
    if seen==int(count) and mode=='before':
        Path(signal_file).write_bytes(b'before\n');os._exit(99)
    value=real(*args,**kwargs)
    if seen==int(count) and mode=='after':
        Path(signal_file).write_bytes(b'after\n');os._exit(99)
    return value
os.rename=rename
sys.path.insert(0,str(Path(module_path).parent))
sys.argv=[module_path,operation,'--job',job]
runpy.run_path(module_path,run_name='__main__')
'''

LOCK = r'''
import json,os,runpy,sys,time
from pathlib import Path
module_path,job,ready,release,deadline=sys.argv[1:]
deadline=float(deadline)
source=json.loads((Path(job)/'state.json').read_bytes())['source']
real=os.rename;held=False
def rename(*args,**kwargs):
    global held
    if not held and (str(args[0])==source or str(args[1])==source):
        held=True;Path(ready).write_bytes(b'writer-before-rename\n')
        while not Path(release).exists():
            if time.monotonic()>=deadline:raise SystemExit(8)
            time.sleep(.01)
    return real(*args,**kwargs)
os.rename=rename
sys.path.insert(0,str(Path(module_path).parent))
sys.argv=[module_path,'adopt','--job',job]
runpy.run_path(module_path,run_name='__main__')
'''



class CompactMigrationTests(unittest.TestCase):
    @contextlib.contextmanager
    def lab(self):
        with tempfile.TemporaryDirectory(prefix='tackle-compact-') as temporary:
            lab = Path(temporary).resolve()
            self.assertFalse(lab.is_relative_to(ROOT), 'native fixture TMPDIR must be outside the repository')
            self.lab_root = lab
            self.serial = 0
            self.records = lab / 'raw'
            self.records.mkdir()
            try:
                yield lab
            finally:
                destination = os.environ.get('TACKLE_MIGRATION_RECORD_DIR')
                if destination:
                    parent = Path(destination)
                    self.assertTrue(parent.is_absolute())
                    self.assertTrue(parent.is_dir())
                    self.assertFalse(parent.is_symlink())
                    self.assertEqual(parent, parent.resolve(), 'controller record root must use canonical no-alias spelling')
                    self.assertFalse(parent.resolve().is_relative_to(lab))
                    shutil.copytree(lab, parent / (self._testMethodName + '-' + uuid.uuid4().hex), symlinks=True)

    def collect_child(self, child, deadline, cancel_groups=()):
        """One absolute observation deadline; cleanup has only its bounded TERM/KILL grace."""
        out, err = b'', b''
        try:
            out, err = child.communicate(timeout=max(0.0, deadline - time.monotonic()))
            return out, err, False, True
        except subprocess.TimeoutExpired as exc:
            out, err = exc.output or b'', exc.stderr or b''
        for action, grace in ((signal.SIGTERM, .5), (signal.SIGKILL, 1.0)):
            for group in {child.pid, *cancel_groups}:
                try:
                    os.killpg(group, action)
                except ProcessLookupError:
                    pass
            try:
                out, err = child.communicate(timeout=max(0.0, deadline + grace - time.monotonic()))
                return out, err, True, True
            except subprocess.TimeoutExpired as exc:
                out, err = exc.output or out, exc.stderr or err
        return out, err, True, False

    def run_child(self, argv, cwd, expected=None, deadline=None, cancel_groups=()):
        self.serial += 1
        capture = self.records / ('child-%04d' % self.serial)
        capture.mkdir()
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        deadline = time.monotonic() + 30 if deadline is None else deadline
        meta = dict(argv=[str(x) for x in argv], cwd=str(cwd), start=started,
                    end=None, exit=None, signal=None, timeout=False, launch_error=None,
                    complete=False, stdout='stdout.bin', stderr='stderr.bin')
        out, err = b'', b''
        child = None
        try:
            if time.monotonic() >= deadline:
                meta['timeout'] = True
            else:
                child = subprocess.Popen(meta['argv'], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         start_new_session=True)
                out, err, meta['timeout'], meta['complete'] = self.collect_child(child, deadline, cancel_groups)
                meta['exit'] = child.poll()
                if meta['exit'] is not None and meta['exit'] < 0:
                    meta['signal'] = -meta['exit']
        except OSError as exc:
            meta['launch_error'] = type(exc).__name__ + ': ' + str(exc)
        finally:
            (capture / 'stdout.bin').write_bytes(out)
            (capture / 'stderr.bin').write_bytes(err)
            meta['end'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            write_json(capture / 'result.json', meta)
        self.assertIsNone(meta['launch_error'], meta)
        self.assertFalse(meta['timeout'], meta)
        self.assertTrue(meta['complete'], meta)
        if expected is not None:
            self.assertEqual(meta['exit'], expected, (meta, out, err))
        return meta, out, err

    def install(self, lab):
        original = current_root(ROOT)
        self.assertTrue((original / 'scripts/migrate/compact.py').is_file(), 'unavailable consumer: compact.py')
        self.assertTrue((original / 'references/guides/migration-catalog.json').is_file(), 'unavailable catalog')
        installed = lab / 'install'
        installed.mkdir()
        shutil.copyfile(original / 'SKILL.md', installed / 'SKILL.md')
        for name in ('scripts', 'references'):
            shutil.copytree(original / name, installed / name, symlinks=True)
        for name, value in ADAPTER_PINS.items():
            self.assertEqual(digest((installed / 'scripts/migrate' / name).read_bytes()), value)
        return installed

    def acceptance_command(self, text, replacement=None):
        sections = list(re.finditer(
            r'^## Acceptance and recovery(?:[ \t]+<!--[^\n]*-->)?[ \t]*\n(?:(?!^## ).)*',
            text, flags=re.M | re.S))
        self.assertEqual(len(sections), 1)
        section = sections[0]
        pattern = r'(^```sh[ \t]*\n)([^\n]+)(\n```[ \t]*(?=\n|\Z))'
        commands = list(re.finditer(pattern, section[0], flags=re.M))
        self.assertEqual(len(commands), 1)
        if replacement is None:
            return commands[0][2]
        updated, count = re.subn(pattern, lambda match: match[1] + replacement + match[3],
                                 section[0], flags=re.M)
        self.assertEqual(count, 1)
        return text[:section.start()] + updated + text[section.end():]

    def fixture(self, lab, name='source', old=True):
        project = lab / name
        project.mkdir()
        base.materialize(project, 'pass-full')
        source = project / 'docs/plans/demo'
        for path in sorted(source.rglob('*'), reverse=True):
            if path.is_file():
                value = path.read_bytes().replace(b'T-' b'01', b'T-0001').replace(b'T-' b'02', b'T-0002')
                path.write_bytes(value)
                if path.name in ('T-' '01.md', 'T-' '02.md', 'T-' '01-report.md'):
                    path.rename(path.with_name(path.name.replace('T-' '01', 'T-0001').replace('T-' '02', 'T-0002')))
        stamp = '10.1.0' if old else '10.3.0'
        (source / 'AGENTS.md').write_text('# Agents\n\n**Methodology: Tackle ' + stamp + '**\n')
        (source / '.context-lock').write_bytes(b'')
        (project / 'neighbor-sentinel').write_bytes(b'neighbor\n')
        (source / 'legacy-kept').mkdir()
        (source / 'legacy-kept/raw.bin').write_bytes(b'unchanged\x00\xff')
        brief = source / 'tasks' / ('{}-{:04d}.md'.format('T', 2))
        text = brief.read_text()
        command = NEXT_TASK_CHECK
        text = re.sub(r'^- \*\*Write scope\*\*:.*$', '- **Write scope**: `owned/check-observed.txt`', text, flags=re.M)
        text = self.acceptance_command(text, command)
        self.assertEqual(self.acceptance_command(text), command)
        brief.write_text(text)
        return project, source

    def context(self, source, next_wave=True, at_boundary=True, requests=(), quiescence='observed-stopped'):
        boundary = {'schema': 'tackle-migration-boundary/1', 'source_sha256': tree_sha(source),
                    'at_boundary': at_boundary, 'quiescence': quiescence,
                    'observer': 'fixture-controller', 'evidence': []}
        value = dict(workspace=source.name, target='10.3.0',
                     next_wave=['{}-{:04d}'.format('T', 2)] if next_wave else [],
                     boundary=dict(at_boundary=at_boundary, source_receipt_sha256=digest(canonical(boundary))),
                     optional_requests=list(requests), date='2026-09-27', run_id='compact-fixture')
        return value, boundary

    def cli(self, installed, operation, args, expected=None, deadline=None, cancel_groups=()):
        return self.run_child([sys.executable, '-I', '-B', installed / 'scripts/migrate/compact.py',
                               operation, *args], self.lab_root, expected, deadline, cancel_groups)

    def plan(self, installed, source, job, next_wave=True, at_boundary=True, requests=(), quiescence='observed-stopped'):
        context, boundary = self.context(source, next_wave, at_boundary, requests, quiescence)
        context_path = job.parent / (job.name + '-context.json')
        manifest = job.parent / (job.name + '-manifest.json')
        write_json(context_path, context)
        before = inventory(source)
        self.cli(installed, 'diagnose', ['--workspace', source, '--target', '10.3.0',
                                       '--context', context_path, '--output', manifest], 0)
        self.assertEqual(inventory(source), before)
        result = read_json(manifest)
        self.assertEqual(result['schema'], 'tackle-migration-plan/1')
        self.assertEqual(result['source']['sha256'], digest(canonical(before)))
        self.assertEqual(result['context'], context)
        self.assertEqual(result['operation_id'], digest(canonical({k: v for k, v in result.items() if k != 'operation_id'})))
        return manifest, result, boundary

    def pure(self, installed, source, context):
        value = {'files': {str(p.relative_to(source)): p.read_bytes().hex()
                          for p in source.rglob('*') if p.is_file()},
                 'context': context, 'catalog': read_json(installed / 'references/guides/migration-catalog.json')}
        input_file = self.lab_root / ('pure-' + uuid.uuid4().hex + '.json')
        output_file = input_file.with_suffix('.out.json')
        write_json(input_file, value)
        bootstrap = input_file.with_suffix('.py'); bootstrap.write_text(PURE)
        before = inventory(source)
        self.run_child([sys.executable, '-I', '-B', bootstrap, installed, input_file, output_file, ROOT], self.lab_root, 0)
        self.assertEqual(inventory(source), before)
        result = read_json(output_file)
        self.assertIsNone(result['source']['path'])
        self.assertIsNone(result['source']['inventory'])
        self.assertIsNone(result['source']['sha256'])
        self.assertTrue(output_file.with_suffix('.reads.json').is_file())
        return result

    def prepared(self, installed, source, job):
        manifest, plan, boundary = self.plan(installed, source, job)
        self.cli(installed, 'prepare', ['--manifest', manifest, '--job', job], 0)
        write_json(job / 'boundary.json', boundary)
        candidate = job / 'candidate-project/docs/plans' / source.name
        pattern = rb'Methodology: Tackle [0-9]+\.[0-9]+\.[0-9]+'
        original_stamp = re.findall(pattern, (source / 'AGENTS.md').read_bytes())
        self.assertEqual(re.findall(pattern, (candidate / 'AGENTS.md').read_bytes()), original_stamp)
        return plan, candidate

    def semantic_edits(self, candidate):
        """Fixture-specific operator edits, never a duplicate structural transformation/adoption engine."""
        task = '{}-{:04d}'.format('T', 1)
        brief = candidate / 'tasks' / (task + '.md')
        baseline = digest(brief.read_bytes())
        report = candidate / 'reports' / (task + '-report.md')
        content = report.read_text()
        marker = '**Brief sha256**: ' + baseline + '\n'
        if marker not in content:
            content = content.replace('**Remains**:', marker + '**Remains**:', 1)
            report.write_text(content)
        history = candidate / 'history.md'
        line = 'Brief sha256 ' + task + ': ' + baseline + '\n'
        if line not in history.read_text():
            history.write_text(history.read_text().rstrip('\n') + '\n' + line)

    def final_receipt(self, installed, source, job, candidate, plan, extra_evidence=()):
        self.assertFalse((candidate / 'owned/check-observed.txt').exists())
        # The first verify freezes/records the lint phases but cannot pass without external semantics.
        self.cli(installed, 'verify', ['--job', job], 1)
        frozen = tree_sha(candidate)
        for phase in ('pre-stamp', 'post-stamp'):
            receipt = read_json(job / 'receipts' / (phase + '.json'))
            self.assertEqual(receipt['schema'], 'tackle-migration-capture/1')
            self.assertEqual(receipt['stage'], phase)
            self.assertEqual(receipt['cwd'], str(job / 'candidate-project'))
            self.assertEqual(receipt['workspace'], str(candidate))
            self.assertEqual([c['row'] for c in receipt['checks']], list(range(1, 20)))
            if phase == 'post-stamp':
                self.assertEqual(receipt['candidate_sha256'], frozen)
            for check in receipt['checks']:
                actual = read_json(job / check['result']['path'])
                self.assertEqual(digest((job / check['result']['path']).read_bytes()), check['result']['sha256'])
                self.assertEqual(actual['argv'], [sys.executable, '-I', str(installed / 'scripts/lint.py'),
                                                  '--row', str(check['row']), candidate.name])
                self.assertEqual(actual['cwd'], str(job / 'candidate-project'))
                self.assertFalse(actual['timeout'])
                self.assertIsNone(actual['signal'])
                self.assertIsNone(actual['launch_error'])
                self.assertTrue(actual['complete'])
                for stream in ('stdout', 'stderr'):
                    self.assertEqual(digest((job / actual[stream]['path']).read_bytes()), actual[stream]['sha256'])
                observed = base.NAMESPACE['lint_verdict'](check['row'],
                    dict(child_exit=actual['exit'], timeout=actual['timeout'], launch_error=actual['launch_error'],
                         signal=actual['signal'], inputs_stable=True, artifacts_present=True),
                    (job / actual['stdout']['path']).read_bytes(), (job / actual['stderr']['path']).read_bytes())
                self.assertEqual(actual['verdict'], observed)
                self.assertIn(observed, {'PASS', 'WARN'} if check['row'] in {8, 13, 15} else {'PASS'})
        observation = job / 'manual-review.json'
        write_json(observation, dict(candidate_sha256=frozen, source_sha256=plan['source']['sha256'],
            consumer='isolated-fixture-reviewer', check_sentinel_absent=True,
            native_lint_receipts=[dict(path='receipts/' + phase + '.json',
                sha256=digest((job / 'receipts' / (phase + '.json')).read_bytes()))
                for phase in ('pre-stamp', 'post-stamp')],
            checkpoint_sha256=tree_sha(job / 'checkpoint'),
            restoration_sha256=tree_sha(job / 'restore-probe')))
        evidence = [dict(path='manual-review.json', sha256=digest(observation.read_bytes())), *extra_evidence]
        receipt = dict(schema='tackle-migration-review/1', reviewer='external-fixture-reviewer',
                       candidate_sha256=frozen, source_sha256=plan['source']['sha256'],
                       catalog_sha256=plan['catalog_sha256'],
                       decisions=[dict(id=x['id'], state='satisfied', evidence=evidence)
                                  for x in plan['obligations'] if (x['kind'] == 'required' or x['family'] in plan['context']['optional_requests']) and x['state'] != 'not-applicable'])
        write_json(job / 'semantic-review.json', receipt)
        self.cli(installed, 'verify', ['--job', job], 0)
        self.assertEqual(tree_sha(candidate), frozen)
        self.assertFalse((candidate / 'owned/check-observed.txt').exists())
        state = read_json(job / 'state.json')
        self.assertEqual(state['phase'], 'verified')
        self.assertEqual(state['candidate_sha256'], frozen)
        self.assertEqual(tree_sha(job / 'restore-probe'), tree_sha(job / 'checkpoint'))
        return frozen

    def ready(self, installed, source, job):
        plan, candidate = self.prepared(installed, source, job)
        self.semantic_edits(candidate)
        frozen = self.final_receipt(installed, source, job, candidate, plan)
        return plan, candidate, frozen

    def test_catalog_preserves_all_obligations_and_supported_origins(self):
        with self.lab() as lab:
            installed = self.install(lab)
            catalog_path = installed / 'references/guides/migration-catalog.json'
            catalog = read_json(catalog_path)
            self.assertEqual(catalog['schema'], 'tackle-migration-catalog/1')
            self.assertEqual(catalog['supported_buckets'], ['pre-3', '3', '4', '5', 'lite'])
            self.assertEqual(catalog['provenance'], PROVENANCE)
            self.assertEqual([x['id'] for x in catalog['rules']], ORDER)
            for i, rule in enumerate(catalog['rules']):
                self.assertEqual(rule['requires'], [] if i == 0 else [ORDER[i - 1]])
            project, source = self.fixture(lab)
            manifest, plan, _ = self.plan(installed, source, lab / 'job')
            self.assertEqual({x['id'] for x in plan['obligations']}, {source_id(x) for x in PROVENANCE['items']})
            self.assertEqual(len(plan['obligations']), 220)
            self.assertNotIn('stamp', [a['effect'] for a in plan['actions'] if a['family'] == 'S'])
            original = catalog_path.read_bytes()
            for kind in ('item', 'group', 'support', 'order'):
                with self.subTest(kind=kind):
                    mutated = json.loads(original)
                    if kind == 'item': mutated['provenance']['items'].pop()
                    if kind == 'group': mutated['provenance']['groups'].pop()
                    if kind == 'support': mutated['supported_buckets'].remove('lite')
                    if kind == 'order': mutated['rules'][4:6] = reversed(mutated['rules'][4:6])
                    write_json(catalog_path, mutated)
                    before = inventory(source)
                    result = self.cli(installed, 'diagnose', ['--workspace', source, '--target', '10.3.0',
                                      '--context', lab / 'job-context.json', '--output', lab / ('bad-' + kind + '.json')])
                    self.assertNotEqual(result[0]['exit'], 0)
                    self.assertEqual(inventory(source), before)
            catalog_path.write_bytes(original)
            # A different key order is a valid representation, not a missing obligation.
            catalog_path.write_text(json.dumps(dict(reversed(list(catalog.items()))), ensure_ascii=False, indent=2) + '\n')
            self.plan(installed, source, lab / 'reordered')

    def test_installed_catalog_is_self_sufficient_without_repository_history(self):
        with self.lab() as lab:
            installed = self.install(lab)
            self.assertFalse((lab / 'maintaining').exists())
            self.assertFalse((lab / 'docs').exists())
            for bucket, fixture in [('pre-3', 'pre3-to-3'), ('3', '3-to-4'), ('4', '4-to-5')]:
                with self.subTest(bucket=bucket):
                    project = lab / ('origin-' + bucket)
                    source = project / 'docs/plans/demo'
                    shutil.copytree(ROOT / 'eval/migration/fixtures' / fixture / 'before', source)
                    manifest, value, _ = self.plan(installed, source, lab / ('job-' + bucket), next_wave=False)
                    self.assertEqual(value['observed']['bucket'], bucket)
                    self.assertEqual(value['context']['optional_requests'], [])
                    pure = self.pure(installed, source, value['context'])
                    self.assertEqual(pure['observed']['bucket'], bucket)
            project, source = self.fixture(lab)
            self.plan(installed, source, lab / 'modern', next_wave=False)
            lite = lab / 'lite-project/docs/plans/lite'
            lite.mkdir(parents=True)
            (lite / 'plan.md').write_text('Gate: Lite\n# Work\n\nOpen remaining work.\n')
            (lite / 'history.md').write_bytes(b'history\n')
            (lite / 'resource-usage.md').write_bytes(b'usage\n')
            self.plan(installed, lite, lab / 'lite-job', next_wave=False)
            broken = installed / 'references/guides/run-card.md'
            broken.unlink()
            before = inventory(source)
            result = self.cli(installed, 'diagnose', ['--workspace', source, '--target', '10.3.0',
                              '--context', lab / 'modern-context.json', '--output', lab / 'missing-resource.json'])
            self.assertNotEqual(result[0]['exit'], 0)
            self.assertEqual(inventory(source), before)

    def test_copy_validation_adopts_current_candidate_and_runs_literal_next_check(self):
        with self.lab() as lab:
            installed = self.install(lab)
            project, source = self.fixture(lab)
            bad_project, bad_source = self.fixture(lab, 'stamp-only')
            bad_before = inventory(bad_source)
            bad_plan, bad_candidate = self.prepared(installed, bad_source, lab / 'stamp-only-job')
            agents = bad_candidate / 'AGENTS.md'
            agents.write_text(agents.read_text().replace('Tackle 10.1.0', 'Tackle 10.3.0'))
            meta, out, err = self.run_child([sys.executable, '-I', str(installed / 'scripts/lint.py'),
                '--row', '14', bad_candidate.name], lab / 'stamp-only-job/candidate-project')
            verdict = base.NAMESPACE['lint_verdict'](14,
                dict(child_exit=meta['exit'], timeout=meta['timeout'], launch_error=meta['launch_error'],
                     signal=meta['signal'], inputs_stable=True, artifacts_present=True), out, err)
            self.assertEqual(verdict, 'FAIL')
            self.assertIn(('missing brief hash: ' + '{}-{:04d}'.format('T', 1)).encode(), out)
            self.cli(installed, 'verify', ['--job', lab / 'stamp-only-job'], 1)
            self.assertEqual(inventory(bad_source), bad_before)
            original = inventory(source)
            closed = (source / 'tasks' / ('{}-{:04d}.md'.format('T', 1))).read_bytes()
            plan, candidate, frozen = self.ready(installed, source, lab / 'job')
            job = lab / 'job'
            self.assertEqual(inventory(source), original)
            self.assertEqual((candidate / 'tasks' / ('{}-{:04d}.md'.format('T', 1))).read_bytes(), closed)
            self.cli(installed, 'adopt', ['--job', job], 0)
            self.assertEqual(read_json(job / 'state.json')['phase'], 'adopted')
            self.assertEqual(tree_sha(source), frozen)
            self.assertEqual(inventory(job / 'original-backup'), original)
            self.assertEqual((project / 'neighbor-sentinel').read_bytes(), b'neighbor\n')
            self.assertFalse((source / 'owned/check-observed.txt').exists())
            receipt_before = inventory(job / 'receipts')
            task = source / 'tasks' / ('{}-{:04d}.md'.format('T', 2))
            command = self.acceptance_command(task.read_text())
            self.assertEqual(command, NEXT_TASK_CHECK)
            _, out, err = self.run_child(shlex.split(command), source, 0)
            self.assertEqual((out, err), (b'', b''))
            self.assertEqual((source / 'owned/check-observed.txt').read_bytes(), b'adopted-check\n')
            self.assertEqual(inventory(job / 'receipts'), receipt_before)
            before_restore = inventory(source)
            self.cli(installed, 'restore', ['--job', job], 1)
            self.assertEqual(inventory(source), before_restore)
            failure_project, failure_source = self.fixture(lab, 'failed-check')
            failure_task = failure_source / 'tasks' / ('{}-{:04d}.md'.format('T', 2))
            old_command = self.acceptance_command(failure_task.read_text())
            self.assertEqual(old_command, NEXT_TASK_CHECK)
            failing_command = "python3 -I -c 'print(\"PASS\");raise SystemExit(7)'"
            failure_task.write_text(self.acceptance_command(failure_task.read_text(), failing_command))
            failure_job = lab / 'failure-job'
            _, _, failed_frozen = self.ready(installed, failure_source, failure_job)
            self.cli(installed, 'adopt', ['--job', failure_job], 0)
            literal = self.acceptance_command((failure_source / 'tasks' / failure_task.name).read_text())
            self.assertEqual(literal, failing_command)
            _, out, err = self.run_child(shlex.split(literal), failure_source, 7)
            self.assertEqual((out, err), (b'PASS\n', b''))
            self.assertEqual(read_json(failure_job / 'state.json')['phase'], 'adopted')
            self.assertEqual(tree_sha(failure_source), failed_frozen)
            self.assertEqual(inventory(job / 'original-backup'), original)

    def test_structural_chain_and_path_refusals_preserve_originals(self):
        with self.lab() as lab:
            installed = self.install(lab)
            for name, fixture in [('pre-3', 'pre3-to-3'), ('3', '3-to-4'), ('4', '4-to-5')]:
                with self.subTest(origin=name):
                    source = lab / ('project-' + name) / 'docs/plans/demo'
                    shutil.copytree(ROOT / 'eval/migration/fixtures' / fixture / 'before', source)
                    (source / 'legacy-existing').mkdir()
                    (source / 'legacy-existing/sentinel').write_bytes(b'legacy\n')
                    before = inventory(source)
                    manifest, plan, _ = self.plan(installed, source, lab / ('job-' + name), next_wave=False)
                    self.cli(installed, 'prepare', ['--manifest', manifest, '--job', lab / ('job-' + name)], 0)
                    candidate = lab / ('job-' + name) / 'candidate-project/docs/plans/demo'
                    self.assertEqual(inventory(source), before)
                    self.assertEqual((candidate / 'legacy-existing/sentinel').read_bytes(), b'legacy\n')
                    self.assertIn('Schema: tackle-workspace/5', (candidate / 'task-board.md').read_text())
                    for relative, entry in before.items():
                        if entry['type'] == 'file' and not relative.startswith('legacy-'):
                            copies = list(candidate.glob('legacy-*/' + relative))
                            self.assertTrue(copies, relative)
                            self.assertTrue(any(digest(x.read_bytes()) == entry['sha256'] for x in copies), relative)
            lite = lab / 'lite-source/docs/plans/lite'
            lite.mkdir(parents=True)
            lite_plan = b'Gate: Lite\n# Remaining work\n\nKeep the selected work.\n'
            (lite / 'plan.md').write_bytes(lite_plan)
            (lite / 'log.md').write_bytes(b'older history\n')
            (lite / 'log-archive.md').write_bytes(b'archived history\n')
            (lite / 'usage.md').write_bytes(b'older usage\n')
            before = inventory(lite)
            manifest, _, _ = self.plan(installed, lite, lab / 'lite-job', next_wave=False)
            self.cli(installed, 'prepare', ['--manifest', manifest, '--job', lab / 'lite-job'], 0)
            lite_copy = lab / 'lite-job/candidate-project/docs/plans/lite'
            self.assertEqual((lite_copy / 'plan.md').read_bytes(), lite_plan)
            self.assertFalse((lite_copy / 'task-board.md').exists())
            for name, expected in [('history.md', b'older history\n'), ('history-archive.md', b'archived history\n'),
                                   ('resource-usage.md', b'older usage\n')]:
                self.assertEqual((lite_copy / name).read_bytes(), expected)
            self.assertEqual(inventory(lite), before)
            project, source = self.fixture(lab, 'paths')
            before = inventory(source)
            alias = lab / 'source-alias'
            alias.symlink_to(source, target_is_directory=True)
            context, _ = self.context(source)
            write_json(lab / 'paths-context.json', context)
            self.cli(installed, 'diagnose', ['--workspace', alias, '--target', '10.3.0',
                                           '--context', lab / 'paths-context.json', '--output', lab / 'alias.json'], 2)
            self.assertEqual(inventory(source), before)
            for conflict in ('collision', 'unclosed-fence', 'external-link'):
                with self.subTest(conflict=conflict):
                    bad = lab / conflict / 'docs/plans/demo'
                    shutil.copytree(source, bad)
                    if conflict == 'collision': (bad / 'board.md').write_bytes(b'unknown\n')
                    if conflict == 'unclosed-fence':
                        with (bad / 'task-board.md').open('a') as f: f.write('\n```markdown\n')
                    if conflict == 'external-link': (bad / 'external').symlink_to(project / 'neighbor-sentinel')
                    snapshot = inventory(bad)
                    context, _ = self.context(bad)
                    context_path = lab / (conflict + '-context.json'); write_json(context_path, context)
                    result = self.cli(installed, 'diagnose', ['--workspace', bad, '--target', '10.3.0',
                                    '--context', context_path, '--output', lab / (conflict + '-manifest.json')])
                    self.assertNotEqual(result[0]['exit'], 0)
                    self.assertEqual(inventory(bad), snapshot)

    def test_repeat_and_interrupted_cutover_reconcile_without_duplicate_effects(self):
        with self.lab() as lab:
            installed = self.install(lab)
            for direction in ('adopt', 'restore'):
                for count in (1, 2):
                    for mode in ('before', 'after'):
                        with self.subTest(direction=direction, rename=count, point=mode):
                            label = '%s-%s-%s' % (direction, count, mode)
                            project, source = self.fixture(lab, label)
                            job = lab / ('job-' + label)
                            plan, candidate, frozen = self.ready(installed, source, job)
                            if direction == 'restore': self.cli(installed, 'adopt', ['--job', job], 0)
                            boot = lab / (label + '.py'); boot.write_text(INTERRUPT)
                            signal_file = lab / (label + '.signal')
                            self.run_child([sys.executable, '-I', '-B', boot, installed / 'scripts/migrate/compact.py',
                                            direction, job, str(count), mode, signal_file], lab, 99)
                            self.assertEqual(signal_file.read_bytes(), (mode + '\n').encode())
                            self.cli(installed, direction, ['--job', job], 0)
                            expected = frozen if direction == 'adopt' else tree_sha(job / 'checkpoint')
                            self.assertEqual(tree_sha(source), expected)
                            before = inventory(job)
                            self.cli(installed, direction, ['--job', job], 0)
                            self.assertEqual(inventory(job), before)
                            self.assertEqual((project / 'neighbor-sentinel').read_bytes(), b'neighbor\n')
            project, source = self.fixture(lab, 'bad-state')
            job = lab / 'bad-state-job'
            self.ready(installed, source, job)
            state = (job / 'state.json').read_bytes()
            (job / 'state.json').write_bytes(b'{')
            before = inventory(source)
            self.cli(installed, 'adopt', ['--job', job], 1)
            self.assertEqual(inventory(source), before)
            (job / 'state.json').write_bytes(state)
            contradictory = json.loads(state)
            contradictory['candidate_sha256'] = '0' * 64
            write_json(job / 'state.json', contradictory)
            self.cli(installed, 'adopt', ['--job', job], 1)
            self.assertEqual(inventory(source), before)
            (job / 'state.json').write_bytes(state)
            self.cli(installed, 'adopt', ['--job', job], 0)

    def test_concurrent_writers_and_rollback_drift_preserve_sentinels(self):
        with self.lab() as lab:
            installed = self.install(lab)
            project, source = self.fixture(lab)
            job = lab / 'job'
            plan, candidate, frozen = self.ready(installed, source, job)
            ready, release = lab / 'locked', lab / 'release'
            boot = lab / 'lock.py'; boot.write_text(LOCK)
            deadline = time.monotonic() + 30
            argv = [sys.executable, '-I', '-B', str(boot), str(installed / 'scripts/migrate/compact.py'),
                    str(job), str(ready), str(release), repr(deadline)]
            holder_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:
                child = subprocess.Popen(argv, cwd=lab, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            except OSError as exc:
                (self.records / 'lock.stdout.bin').write_bytes(b'')
                (self.records / 'lock.stderr.bin').write_bytes(b'')
                write_json(self.records / 'lock.result.json', dict(argv=argv, cwd=str(lab), start=holder_start,
                    end=datetime.datetime.now(datetime.timezone.utc).isoformat(), exit=None, signal=None,
                    timeout=False, complete=False, launch_error=type(exc).__name__ + ': ' + str(exc)))
                raise
            try:
                while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                    time.sleep(min(.01, max(0.0, deadline - time.monotonic())))
                self.assertTrue(ready.is_file(), 'actual adoption writer failed to reach its locked rename boundary')
                before = inventory(source)
                self.cli(installed, 'adopt', ['--job', job], 1, deadline=deadline, cancel_groups=(child.pid,))
                self.assertEqual(inventory(source), before)
            finally:
                if time.monotonic() < deadline:
                    release.write_bytes(b'release\n')
                out, err, timeout, complete = self.collect_child(child, deadline)
                (self.records / 'lock.stdout.bin').write_bytes(out)
                (self.records / 'lock.stderr.bin').write_bytes(err)
                write_json(self.records / 'lock.result.json', dict(argv=argv, cwd=str(lab), start=holder_start,
                    end=datetime.datetime.now(datetime.timezone.utc).isoformat(), exit=child.poll(),
                    timeout=timeout, complete=complete, signal=-child.returncode if child.returncode and child.returncode < 0 else None,
                    launch_error=None, stdout='lock.stdout.bin', stderr='lock.stderr.bin'))
                self.assertFalse(timeout)
                self.assertTrue(complete)
                self.assertEqual(child.returncode, 0, (out, err))
            self.cli(installed, 'adopt', ['--job', job], 0)
            self.cli(installed, 'restore', ['--job', job], 0)
            self.assertEqual(tree_sha(source), plan['source']['sha256'])
            project, source = self.fixture(lab, 'drift')
            job = lab / 'drift-job'
            self.ready(installed, source, job)
            (source / 'concurrent-edit').write_bytes(b'drift\n')
            before = inventory(source)
            self.cli(installed, 'adopt', ['--job', job], 1)
            self.assertEqual(inventory(source), before)
            self.assertEqual((project / 'neighbor-sentinel').read_bytes(), b'neighbor\n')

    def test_record_lineage_and_optional_capabilities_remain_scoped(self):
        with self.lab() as lab:
            installed = self.install(lab)
            faults = (
                ('unknown-remains', 'H', 'v9.0 → v9.1 checklist', 3, 'R', 'unknown'),
                ('mismatched-baseline', 'G', 'v10.1 → v10.2 checklist', 3, 'R', 'pending'),
                ('illegal-outcome', 'H', 'v9.0.0 → v9.0.1 checklist', 6, 'E', 'pending'),
                ('no-boundary', 'G', 'v10.1 → v10.2 checklist', 1, 'P', 'pending'),
                ('unknown-quiescence', 'G', 'v10.1 → v10.2 checklist', 1, 'P', 'unknown'),
                ('copied-consent', 'G', 'v9.3 → v10.0 checklist', 5, 'J', 'unknown'),
            )
            causal_origins = {
                'unknown-remains': [('H', 'v9.0 → v9.1 checklist', 3)],
                'mismatched-baseline': [('G', 'v10.1 → v10.2 checklist', 3)],
                'illegal-outcome': [('H', 'v9.0.0 → v9.0.1 checklist', 6)],
                'no-boundary': [('G', 'v10.1 → v10.2 checklist', 1), ('H', 'v8.3 → v8.4 checklist', 1)],
                'unknown-quiescence': [('G', 'v10.1 → v10.2 checklist', 1), ('H', 'v8.3 → v8.4 checklist', 1)],
                'copied-consent': [('G', 'v9.3 → v10.0 checklist', 5), ('G', 'v10.0 → v10.1 checklist', 9),
                                   ('H', 'v9.1.0 → v9.1.1 checklist', 4), ('H', 'v9.0 → v9.1 checklist', 7)],
            }
            for fault, origin, heading, item, family, pending_state in faults:
                with self.subTest(fault=fault):
                    affected_id = json.dumps([origin, heading, item], ensure_ascii=False, separators=(',', ':'))
                    causal_ids = {json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in causal_origins[fault]}
                    self.assertIn(affected_id, causal_ids)
                    self.assertTrue(causal_ids <= {source_id(x) for x in PROVENANCE['items']})
                    self.assertIn(affected_id, [source_id(x) for x in PROVENANCE['items'] if x['family'] == family])
                    project, source = self.fixture(lab, fault)
                    self.semantic_edits(source)
                    closed = '{}-{:04d}'.format('T', 1)
                    answer = 'System One consent: yes · date=2026-09-27 · actor="fixture owner"\n'
                    requests = ('J',) if fault == 'copied-consent' else ()
                    if requests:
                        with (source / 'AGENTS.md').open('a') as f:
                            f.write('\nTypeSafe System One\n' + answer)
                    healthy = {str(x.relative_to(source)): x.read_bytes() for x in source.rglob('*') if x.is_file()}
                    source_facts = dict(fault=fault, obligation=affected_id, causal_origins=sorted(causal_ids), state=pending_state,
                                        original_answer='selected-owner' if requests else 'not-applicable')
                    # One defect is planted before context/source/operation identity is computed.
                    if fault == 'unknown-remains':
                        path = source / 'reports' / (closed + '-report.md')
                        old = path.read_text(); new, count = re.subn(r'^\*\*Remains\*\*:.*$', '**Remains**: unknown', old, count=1, flags=re.M)
                        self.assertEqual(count, 1); path.write_text(new)
                    elif fault == 'mismatched-baseline':
                        path = source / 'reports' / (closed + '-report.md')
                        old = path.read_text(); known = digest((source / 'tasks' / (closed + '.md')).read_bytes())
                        self.assertEqual(old.count('**Brief sha256**: ' + known), 1)
                        path.write_text(old.replace('**Brief sha256**: ' + known, '**Brief sha256**: ' + '0' * 64, 1))
                    elif fault == 'illegal-outcome':
                        path = source / 'resource-usage.md'; old = path.read_text()
                        lines = old.splitlines(keepends=True)
                        header = next(x for x in lines if x.startswith('| Run ID |'))
                        columns = [x.strip() for x in header.strip().split('|')[1:-1]]
                        outcome, event = columns.index('Outcome') + 1, columns.index('Event') + 1
                        changed = 0
                        for number, line in enumerate(lines):
                            cells = line.split('|')
                            if len(cells) == len(columns) + 2 and cells[event].strip() == 'finish':
                                self.assertEqual(cells[outcome].strip(), 'success')
                                cells[outcome] = cells[outcome].replace('success', 'successish', 1)
                                lines[number] = '|'.join(cells); changed += 1
                        self.assertEqual(changed, 1); path.write_text(''.join(lines))
                    elif fault == 'copied-consent':
                        foreign = lab / ('foreign-' + fault + '.md'); foreign.write_text(answer)
                        agents = source / 'AGENTS.md'
                        agents.write_text(agents.read_text().replace(answer, foreign.read_text(), 1))
                        self.assertEqual((source / 'AGENTS.md').read_text().count(answer), 1)
                        source_facts['original_answer'] = 'foreign-workspace; selected owner answer unknown'
                        source_facts['foreign_answer'] = dict(path=str(foreign), sha256=digest(foreign.read_bytes()))
                    job = lab / ('job-' + fault)
                    # The repaired twin differs only in the planted source/context/authority fact.
                    control_project, control_source = self.fixture(lab, 'repaired-' + fault)
                    for name, value in healthy.items():
                        path = control_source / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(value)
                    self.assertEqual({str(x.relative_to(control_source)): x.read_bytes() for x in control_source.rglob('*') if x.is_file()}, healthy)
                    control_job = lab / ('repaired-job-' + fault)
                    cm, cp, cb = self.plan(installed, control_source, control_job, requests=requests)
                    self.cli(installed, 'prepare', ['--manifest', cm, '--job', control_job], 0)
                    write_json(control_job / 'boundary.json', cb)
                    control_candidate = control_job / 'candidate-project/docs/plans' / control_source.name
                    owner = control_job / 'selected-owner-observation.json'
                    write_json(owner, dict(source_sha256=cp['source']['sha256'],
                        answer='selected-owner' if requests else 'not-applicable',
                        consent_line=answer if requests else None, observer='isolated-fixture-controller'))
                    control_frozen = self.final_receipt(installed, control_source, control_job, control_candidate, cp,
                        [dict(path='selected-owner-observation.json', sha256=digest(owner.read_bytes()))])
                    self.assertEqual(read_json(control_job / 'state.json')['phase'], 'verified')
                    self.assertEqual(tree_sha(control_candidate), control_frozen)
                    source_facts['repaired_control'] = dict(path=str(control_job / 'semantic-review.json'),
                        sha256=digest((control_job / 'semantic-review.json').read_bytes()))
                    observed_files = {str(x.relative_to(source)): x.read_bytes() for x in source.rglob('*') if x.is_file()}
                    changed = [name for name in sorted(healthy) if healthy[name] != observed_files[name]]
                    expected_path = {'unknown-remains': 'reports/' + closed + '-report.md',
                                     'mismatched-baseline': 'reports/' + closed + '-report.md',
                                     'illegal-outcome': 'resource-usage.md'}.get(fault)
                    self.assertEqual(set(observed_files), set(healthy))
                    self.assertEqual(changed, [expected_path] if expected_path else [])
                    source_facts['source_sha256'] = tree_sha(source)
                    source_facts['healthy_files'] = {name: digest(value) for name, value in healthy.items()}
                    source_facts['observed_files'] = {name: digest(value) for name, value in observed_files.items()}
                    source_facts['changed_paths'] = changed
                    source_facts['source_evidence'] = [dict(path=str(source / name), sha256=digest(observed_files[name]))
                                                       for name in (changed + (['AGENTS.md'] if requests else []))]
                    source_facts['boundary_fact'] = dict(at_boundary=fault != 'no-boundary',
                        quiescence='unknown' if fault == 'unknown-quiescence' else 'observed-stopped')
                    observation = lab / (fault + '-source-observation.json')
                    write_json(observation, source_facts)
                    manifest, plan, boundary = self.plan(installed, source, job,
                        at_boundary=fault != 'no-boundary', requests=requests,
                        quiescence='unknown' if fault == 'unknown-quiescence' else 'observed-stopped')
                    affected = [x for x in plan['obligations'] if x['id'] in causal_ids or causal_ids.intersection(x['sources'])]
                    self.assertTrue(affected)
                    covered = {name for x in affected for name in [x['id'], *x['sources']]}
                    self.assertTrue(causal_ids <= covered)
                    self.assertTrue(any(x['family'] == family for x in affected))
                    if fault != 'copied-consent':
                        self.assertTrue(any(x['state'] in {'pending', 'unknown'} for x in affected), affected)
                    self.cli(installed, 'prepare', ['--manifest', manifest, '--job', job], 0)
                    write_json(job / 'boundary.json', boundary)
                    candidate = job / 'candidate-project/docs/plans' / source.name
                    # This call is only stage preparation; its absent-review exit has no causal credit.
                    first = self.serial + 1
                    self.cli(installed, 'verify', ['--job', job], 1)
                    frozen = tree_sha(candidate)
                    reached = [dict(path=str(x.relative_to(job)), sha256=digest(x.read_bytes()))
                               for x in sorted((job / 'receipts').rglob('*')) if x.is_file()] if (job / 'receipts').is_dir() else []
                    first_raw = self.records / ('child-%04d' % first)
                    observation_ref = dict(path=str(observation), sha256=digest(observation.read_bytes()))
                    evidence = job / 'fault-review.json'
                    write_json(evidence, dict(candidate_sha256=frozen, source_sha256=plan['source']['sha256'],
                        catalog_sha256=plan['catalog_sha256'], affected_obligation=affected_id, state=pending_state,
                        observation=observation_ref, actual_stage_receipts=reached,
                        preparation_capture=[dict(path=str(first_raw / name), sha256=digest((first_raw / name).read_bytes()))
                                             for name in ('result.json', 'stdout.bin', 'stderr.bin')],
                        repaired_control=source_facts['repaired_control']))
                    evidence_ref = dict(path='fault-review.json', sha256=digest(evidence.read_bytes()))
                    # Physical S/A/V/Z facts still need their own real checks. No false post-stamp PASS is invented.
                    semantic = [x for x in plan['obligations'] if x['state'] != 'not-applicable'
                        and x['family'] not in {'S', 'A', 'V', 'Z'}
                        and (x['kind'] == 'required' or x['family'] in requests)]
                    unresolved = {x['id'] for x in affected}
                    self.assertTrue(unresolved <= {x['id'] for x in semantic})
                    decisions = [dict(id=x['id'], state=pending_state if x['id'] in unresolved else 'satisfied',
                                      evidence=[evidence_ref, observation_ref]) for x in semantic]
                    self.assertEqual({x['id'] for x in decisions if x['state'] in {'pending', 'unknown'}}, unresolved)
                    review = dict(schema='tackle-migration-review/1', reviewer='external-fixture-reviewer',
                        candidate_sha256=frozen, source_sha256=plan['source']['sha256'],
                        catalog_sha256=plan['catalog_sha256'], decisions=decisions)
                    write_json(job / 'semantic-review.json', review)
                    receipt_bytes = (job / 'semantic-review.json').read_bytes()
                    result = self.cli(installed, 'verify', ['--job', job], 1)
                    diagnostic = (result[1] + b'\n' + result[2]).splitlines()
                    self.assertTrue(any(affected_id.encode() in line and pending_state.encode() in line
                        and b'semantic-review.json' in line for line in diagnostic), (fault, result))
                    self.assertEqual(tree_sha(candidate), frozen)
                    self.assertEqual((job / 'semantic-review.json').read_bytes(), receipt_bytes)
                    self.assertEqual(tree_sha(source), plan['source']['sha256'])
                    for ref in (evidence_ref, observation_ref):
                        path = Path(ref['path']) if Path(ref['path']).is_absolute() else job / ref['path']
                        self.assertEqual(digest(path.read_bytes()), ref['sha256'])
            project, source = self.fixture(lab, 'valid')
            plan, candidate, frozen = self.ready(installed, source, lab / 'valid-job')
            self.assertEqual(plan['context']['optional_requests'], [])
            for family in ('J', 'W', 'O'):
                rows = [x for x in plan['obligations'] if x['family'] == family]
                self.assertTrue(rows)
                self.assertTrue(all(x['state'] == 'not-applicable' for x in rows), rows)
            receipt = lab / 'valid-job/semantic-review.json'
            original_receipt = receipt.read_bytes()
            wrong = read_json(receipt); wrong['candidate_sha256'] = '0' * 64
            write_json(receipt, wrong)
            self.cli(installed, 'adopt', ['--job', lab / 'valid-job'], 1)
            self.assertEqual(tree_sha(source), plan['source']['sha256'])
            receipt.write_bytes(original_receipt)
            post = read_json(lab / 'valid-job/receipts/post-stamp.json')
            result = read_json(lab / 'valid-job' / post['checks'][0]['result']['path'])
            raw = lab / 'valid-job' / result['stdout']['path']
            raw.write_bytes(raw.read_bytes() + b'capture-drift\n')
            self.cli(installed, 'adopt', ['--job', lab / 'valid-job'], 1)
            self.assertEqual(tree_sha(source), plan['source']['sha256'])

    def test_catalog_release_gates_discriminate_fault_and_valid_representation(self):
        with self.lab() as lab:
            self.install(lab)
            repo = lab / 'repo'
            (repo / 'maintaining').mkdir(parents=True)
            shutil.copytree(current_root(ROOT), repo / 'skills/tackle', symlinks=True)
            shutil.copyfile(ROOT / 'maintaining/check_migration_catalog.py', repo / 'maintaining/check_migration_catalog.py')
            shutil.copyfile(ROOT / 'maintaining/migrations.md', repo / 'maintaining/migrations.md')
            text = (ROOT / 'MAINTAINING.md').read_text()
            loader = runpy.run_path(str(ROOT / 'eval/validation-integrity/acceptance.py'))['canonical_gates']
            command = loader(text)[3]
            self.assertIn('maintaining/check_migration_catalog.py --repo .', command)
            self.run_child(['sh', '-c', command], repo, 0)
            catalog_path = repo / 'skills/tackle/references/guides/migration-catalog.json'
            original = catalog_path.read_bytes()
            for fault in ('instruction', 'support', 'target'):
                with self.subTest(fault=fault):
                    value = json.loads(original)
                    if fault == 'instruction': value['rules'][4]['instructions'] = []
                    if fault == 'support': value['supported_buckets'].remove('pre-3')
                    if fault == 'target': value['target_methodology'] = '99.0.0'
                    write_json(catalog_path, value)
                    result = self.run_child(['sh', '-c', command], repo)
                    self.assertNotEqual(result[0]['exit'], 0)
            catalog_path.write_bytes(original)
            value = json.loads(original)
            catalog_path.write_text(json.dumps(value, ensure_ascii=False, indent=3) + '\n')
            self.run_child(['sh', '-c', command], repo, 0)
            archive = repo / 'maintaining/migrations.md'
            self.assertEqual(digest(archive.read_bytes()[:ARCHIVE_PREFIX['bytes']]), ARCHIVE_PREFIX['sha256'])
            self.assertIn(GUIDE_SNAPSHOT, archive.read_bytes())
            with archive.open('ab') as f: f.write(b'\nAdditional historical context.\n')
            self.run_child(['sh', '-c', command], repo, 0)

    def test_absolute_evidence_is_read_only_under_the_working_directory_job_or_source(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('compact_confinement', current_root(ROOT) / 'scripts/migrate/compact.py')
        compact = importlib.util.module_from_spec(spec); spec.loader.exec_module(compact)
        with tempfile.TemporaryDirectory(prefix='tackle-confine-') as temporary:
            lab = Path(temporary).resolve()
            work, job, source, outside = lab / 'work', lab / 'job', lab / 'source', lab / 'outside'
            for directory in (work, job, source, outside): directory.mkdir()
            state = dict(source=str(source), original_backup=str(job / 'original-backup'), phase='prepared')
            files = {name: root / (name + '.json') for name, root in
                     (('work', work), ('job', job), ('source', source), ('outside', outside))}
            for name, path in files.items(): path.write_bytes(b'{"evidence": "%s"}\n' % name.encode())
            previous = os.getcwd()
            os.chdir(work)
            try:
                for name in ('work', 'job', 'source'):
                    with self.subTest(admitted=name):
                        ref = dict(path=str(files[name]), sha256=digest(files[name].read_bytes()))
                        self.assertEqual(compact._evidence_ref(job, state, ref), ref)
                # The right and the wrong hash give the same refusal, so no host file can be probed.
                for sha in (digest(files['outside'].read_bytes()), '0' * 64):
                    with self.subTest(refused=sha[:8]):
                        with self.assertRaisesRegex(compact.MigrationError, '^external-evidence-outside-root$'):
                            compact._evidence_ref(job, state, dict(path=str(files['outside']), sha256=sha))
                # A sibling that only shares the job's name prefix, and an alias inside an admitted root, stay outside.
                sibling = lab / 'job2'; sibling.mkdir(); (sibling / 'evidence.json').write_bytes(b'{}\n')
                (work / 'alias.json').symlink_to(files['outside'])
                for path in (sibling / 'evidence.json', work / 'alias.json'):
                    with self.subTest(outside=path.name):
                        with self.assertRaises(compact.MigrationError):
                            compact._evidence_ref(job, state, dict(path=str(path), sha256=digest(path.read_bytes())))
                for raw in (str(work / '..' / 'outside' / 'outside.json'), '../outside/outside.json'):
                    with self.subTest(escape=raw):
                        with self.assertRaises(compact.MigrationError):
                            compact._evidence_path(job, state, raw)
            finally:
                os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
