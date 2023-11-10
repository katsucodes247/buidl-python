from io import BytesIO
from unittest import TestCase

from buidl.ecc import S256Point, PrivateKey
from buidl.helper import (
    big_endian_to_int,
    encode_varstr,
)
from buidl.script import Script, ScriptPubKey
from buidl.taproot import (
    ControlBlock,
    TapLeaf,
    TapBranch,
    TapScript,
)
from buidl.tx import Tx
from buidl.witness import Witness


class TaprootTest(TestCase):
    def test_hd(self):
        point = S256Point.parse_xonly(
            bytes.fromhex(
                "cc8a4bc64d897bddc5fbc2f670f7a8ba0b386779106cf1223c6fc5d7cd6fc115"
            )
        )
        self.assertEqual(
            point.tweaked_key().xonly().hex(),
            "a60869f0dbcf1dc659c9cecbaf8050135ea9e8cdc487053f1dc6880949dc684c",
        )

    def test_p2tr_validation(self):
        tests = [
            "01000000000101d1f1c1f8cdf6759167b90f52c9ad358a369f95284e841d7a2536cef31c0549580100000000fdffffff020000000000000000316a2f49206c696b65205363686e6f7272207369677320616e6420492063616e6e6f74206c69652e204062697462756734329e06010000000000225120a37c3903c8d0db6512e2b40b0dffa05e5a3ab73603ce8c9c4b7771e5412328f90140a60c383f71bac0ec919b1d7dbc3eb72dd56e7aa99583615564f9f99b8ae4e837b758773a5b2e4c51348854c8389f008e05029db7f464a5ff2e01d5e6e626174affd30a00",
            "020000000001027bc0bba407bc67178f100e352bf6e047fae4cbf960d783586cb5e430b3b700e70000000000feffffff7bc0bba407bc67178f100e352bf6e047fae4cbf960d783586cb5e430b3b700e70100000000feffffff01b4ba0e0000000000160014173fd310e9db2c7e9550ce0f03f1e6c01d833aa90140134896c42cd95680b048845847c8054756861ffab7d4abab72f6508d67d1ec0c590287ec2161dd7884983286e1cd56ce65c08a24ee0476ede92678a93b1b180c03407b5d614a4610bf9196775791fcc589597ca066dcd10048e004cd4c7341bb4bb90cee4705192f3f7db524e8067a5222c7f09baf29ef6b805b8327ecd1e5ab83ca2220f5b059b9a72298ccbefff59d9b943f7e0fc91d8a3b944a95e7b6390cc99eb5f4ac41c0d9dfdf0fe3c83e9870095d67fff59a8056dad28c6dfb944bb71cf64b90ace9a7776b22a1185fb2dc9524f6b178e2693189bf01655d7f38f043923668dc5af45bffd30a00",
            "02000000000101b41b20295ac85fd2ae3e3d02900f1a1e7ddd6139b12e341386189c03d6f5795b0000000000fdffffff0100000000000000003c6a3a546878205361746f7368692120e2889e2f32316d696c20466972737420546170726f6f74206d756c7469736967207370656e64202d426974476f044123b1d4ff27b16af4b0fcb9672df671701a1a7f5a6bb7352b051f461edbc614aa6068b3e5313a174f90f3d95dc4e06f69bebd9cf5a3098fde034b01e69e8e788901400fd4a0d3f36a1f1074cb15838a48f572dc18d412d0f0f0fc1eeda9fa4820c942abb77e4d1a3c2b99ccf4ad29d9189e6e04a017fe611748464449f681bc38cf394420febe583fa77e49089f89b78fa8c116710715d6e40cc5f5a075ef1681550dd3c4ad20d0fa46cb883e940ac3dc5421f05b03859972639f51ed2eccbf3dc5a62e2e1b15ac41c02e44c9e47eaeb4bb313adecd11012dfad435cd72ce71f525329f24d75c5b9432774e148e9209baf3f1656a46986d5f38ddf4e20912c6ac28f48d6bf747469fb100000000",
            "010000000001022373cf02ce7df6500ae46a4a0fbbb1b636d2debed8f2df91e2415627397a34090000000000fdffffff88c23d928893cd3509845516cf8411b7cab2738c054cc5ce7e4bde9586997c770000000000fdffffff0200000000000000002b6a29676d20746170726f6f7420f09fa5952068747470733a2f2f626974636f696e6465766b69742e6f72676e9e1100000000001976a91405070d0290da457409a37db2e294c1ffbc52738088ac04410adf90fd381d4a13c3e73740b337b230701189ed94abcb4030781635f035e6d3b50b8506470a68292a2bc74745b7a5732a28254b5f766f09e495929ec308090b01004620c13e6d193f5d04506723bd67abcc5d31b610395c445ac6744cb0a1846b3aabaeac20b0e2e48ad7c3d776cf6f2395c504dc19551268ea7429496726c5d5bf72f9333cba519c21c0000000000000000000000000000000000000000000000000000000000000000104414636070d21adc8280735383102f7a0f5978cea257777a23934dd3b458b79bf388aca218e39e23533a059da173e402c4fc5e3375e1f839efb22e9a5c2a815b07301004620c13e6d193f5d04506723bd67abcc5d31b610395c445ac6744cb0a1846b3aabaeac20b0e2e48ad7c3d776cf6f2395c504dc19551268ea7429496726c5d5bf72f9333cba519c21c0000000000000000000000000000000000000000000000000000000000000000100000000",
        ]
        for i, hex_tx in enumerate(tests):
            tx_obj = Tx.parse(BytesIO(bytes.fromhex(hex_tx)))
            self.assertTrue(tx_obj.verify())

    def test_p2tr_empty_script_tree(self):
        tests = [
            {
                "given": {
                    "internalPubkey": "d6889cb081036e0faefa3a35157ad71086b123b2b144b649798b494c300a961d",
                },
                "intermediary": {
                    "tweak": "b86e7be8f39bab32a6f2c0443abbc210f0edac0e2c53d501b36b64437d9c6c70",
                    "tweakedPubkey": "53a1f6e454df1aa2776a2814a721372d6258050de330b3c6d10ee8f4e0dda343",
                },
                "expected": {
                    "scriptPubKey": "512053a1f6e454df1aa2776a2814a721372d6258050de330b3c6d10ee8f4e0dda343",
                    "bip350Address": "bc1p2wsldez5mud2yam29q22wgfh9439spgduvct83k3pm50fcxa5dps59h4z5",
                },
            },
        ]
        for test in tests:
            point = S256Point.parse_xonly(
                bytes.fromhex(test["given"]["internalPubkey"])
            )
            raw_tweak = bytes.fromhex(test["intermediary"]["tweak"])
            self.assertEqual(point.tweak(), raw_tweak)
            external_pubkey_want = S256Point.parse_xonly(
                bytes.fromhex(test["intermediary"]["tweakedPubkey"])
            )
            external_pubkey = point.tweaked_key(tweak=raw_tweak)
            self.assertEqual(external_pubkey.xonly(), external_pubkey_want.xonly())
            script_pubkey_want = bytes.fromhex(test["expected"]["scriptPubKey"])
            self.assertEqual(
                point.p2tr_script(tweak=raw_tweak).raw_serialize(), script_pubkey_want
            )
            self.assertEqual(
                point.p2tr_address(tweak=raw_tweak), test["expected"]["bip350Address"]
            )

    def test_p2tr_general(self):
        tests = [
            {
                "given": {
                    "internalPubkey": "187791b6f712a8ea41c8ecdd0ee77fab3e85263b37e1ec18a3651926b3a6cf27",
                    "scriptTree": {
                        "id": 0,
                        "script": "20d85a959b0290bf19bb89ed43c916be835475d013da4b362117393e25a48229b8ac",
                        "leafVersion": 192,
                    },
                },
                "intermediary": {
                    "leafHashes": [
                        "5b75adecf53548f3ec6ad7d78383bf84cc57b55a3127c72b9a2481752dd88b21"
                    ],
                    "merkleRoot": "5b75adecf53548f3ec6ad7d78383bf84cc57b55a3127c72b9a2481752dd88b21",
                    "tweak": "cbd8679ba636c1110ea247542cfbd964131a6be84f873f7f3b62a777528ed001",
                    "tweakedPubkey": "147c9c57132f6e7ecddba9800bb0c4449251c92a1e60371ee77557b6620f3ea3",
                },
                "expected": {
                    "scriptPubKey": "5120147c9c57132f6e7ecddba9800bb0c4449251c92a1e60371ee77557b6620f3ea3",
                    "bip350Address": "bc1pz37fc4cn9ah8anwm4xqqhvxygjf9rjf2resrw8h8w4tmvcs0863sa2e586",
                    "scriptPathControlBlocks": [
                        "c1187791b6f712a8ea41c8ecdd0ee77fab3e85263b37e1ec18a3651926b3a6cf27"
                    ],
                },
            },
            {
                "given": {
                    "internalPubkey": "93478e9488f956df2396be2ce6c5cced75f900dfa18e7dabd2428aae78451820",
                    "scriptTree": {
                        "id": 0,
                        "script": "20b617298552a72ade070667e86ca63b8f5789a9fe8731ef91202a91c9f3459007ac",
                        "leafVersion": 192,
                    },
                },
                "intermediary": {
                    "leafHashes": [
                        "c525714a7f49c28aedbbba78c005931a81c234b2f6c99a73e4d06082adc8bf2b"
                    ],
                    "merkleRoot": "c525714a7f49c28aedbbba78c005931a81c234b2f6c99a73e4d06082adc8bf2b",
                    "tweak": "6af9e28dbf9d6aaf027696e2598a5b3d056f5fd2355a7fd5a37a0e5008132d30",
                    "tweakedPubkey": "e4d810fd50586274face62b8a807eb9719cef49c04177cc6b76a9a4251d5450e",
                },
                "expected": {
                    "scriptPubKey": "5120e4d810fd50586274face62b8a807eb9719cef49c04177cc6b76a9a4251d5450e",
                    "bip350Address": "bc1punvppl2stp38f7kwv2u2spltjuvuaayuqsthe34hd2dyy5w4g58qqfuag5",
                    "scriptPathControlBlocks": [
                        "c093478e9488f956df2396be2ce6c5cced75f900dfa18e7dabd2428aae78451820"
                    ],
                },
            },
            {
                "given": {
                    "internalPubkey": "ee4fe085983462a184015d1f782d6a5f8b9c2b60130aff050ce221ecf3786592",
                    "scriptTree": [
                        {
                            "id": 0,
                            "script": "20387671353e273264c495656e27e39ba899ea8fee3bb69fb2a680e22093447d48ac",
                            "leafVersion": 192,
                        },
                        {"id": 1, "script": "06424950333431", "leafVersion": 250},
                    ],
                },
                "intermediary": {
                    "leafHashes": [
                        "8ad69ec7cf41c2a4001fd1f738bf1e505ce2277acdcaa63fe4765192497f47a7",
                        "f224a923cd0021ab202ab139cc56802ddb92dcfc172b9212261a539df79a112a",
                    ],
                    "merkleRoot": "6c2dc106ab816b73f9d07e3cd1ef2c8c1256f519748e0813e4edd2405d277bef",
                    "tweak": "9e0517edc8259bb3359255400b23ca9507f2a91cd1e4250ba068b4eafceba4a9",
                    "tweakedPubkey": "712447206d7a5238acc7ff53fbe94a3b64539ad291c7cdbc490b7577e4b17df5",
                },
                "expected": {
                    "scriptPubKey": "5120712447206d7a5238acc7ff53fbe94a3b64539ad291c7cdbc490b7577e4b17df5",
                    "bip350Address": "bc1pwyjywgrd0ffr3tx8laflh6228dj98xkjj8rum0zfpd6h0e930h6saqxrrm",
                    "scriptPathControlBlocks": [
                        "c0ee4fe085983462a184015d1f782d6a5f8b9c2b60130aff050ce221ecf3786592f224a923cd0021ab202ab139cc56802ddb92dcfc172b9212261a539df79a112a",
                        "faee4fe085983462a184015d1f782d6a5f8b9c2b60130aff050ce221ecf37865928ad69ec7cf41c2a4001fd1f738bf1e505ce2277acdcaa63fe4765192497f47a7",
                    ],
                },
            },
            {
                "given": {
                    "internalPubkey": "f9f400803e683727b14f463836e1e78e1c64417638aa066919291a225f0e8dd8",
                    "scriptTree": [
                        {
                            "id": 0,
                            "script": "2044b178d64c32c4a05cc4f4d1407268f764c940d20ce97abfd44db5c3592b72fdac",
                            "leafVersion": 192,
                        },
                        {"id": 1, "script": "07546170726f6f74", "leafVersion": 192},
                    ],
                },
                "intermediary": {
                    "leafHashes": [
                        "64512fecdb5afa04f98839b50e6f0cb7b1e539bf6f205f67934083cdcc3c8d89",
                        "2cb2b90daa543b544161530c925f285b06196940d6085ca9474d41dc3822c5cb",
                    ],
                    "merkleRoot": "ab179431c28d3b68fb798957faf5497d69c883c6fb1e1cd9f81483d87bac90cc",
                    "tweak": "639f0281b7ac49e742cd25b7f188657626da1ad169209078e2761cefd91fd65e",
                    "tweakedPubkey": "77e30a5522dd9f894c3f8b8bd4c4b2cf82ca7da8a3ea6a239655c39c050ab220",
                },
                "expected": {
                    "scriptPubKey": "512077e30a5522dd9f894c3f8b8bd4c4b2cf82ca7da8a3ea6a239655c39c050ab220",
                    "bip350Address": "bc1pwl3s54fzmk0cjnpl3w9af39je7pv5ldg504x5guk2hpecpg2kgsqaqstjq",
                    "scriptPathControlBlocks": [
                        "c1f9f400803e683727b14f463836e1e78e1c64417638aa066919291a225f0e8dd82cb2b90daa543b544161530c925f285b06196940d6085ca9474d41dc3822c5cb",
                        "c1f9f400803e683727b14f463836e1e78e1c64417638aa066919291a225f0e8dd864512fecdb5afa04f98839b50e6f0cb7b1e539bf6f205f67934083cdcc3c8d89",
                    ],
                },
            },
            {
                "given": {
                    "internalPubkey": "e0dfe2300b0dd746a3f8674dfd4525623639042569d829c7f0eed9602d263e6f",
                    "scriptTree": [
                        {
                            "id": 0,
                            "script": "2072ea6adcf1d371dea8fba1035a09f3d24ed5a059799bae114084130ee5898e69ac",
                            "leafVersion": 192,
                        },
                        [
                            {
                                "id": 1,
                                "script": "202352d137f2f3ab38d1eaa976758873377fa5ebb817372c71e2c542313d4abda8ac",
                                "leafVersion": 192,
                            },
                            {
                                "id": 2,
                                "script": "207337c0dd4253cb86f2c43a2351aadd82cccb12a172cd120452b9bb8324f2186aac",
                                "leafVersion": 192,
                            },
                        ],
                    ],
                },
                "intermediary": {
                    "leafHashes": [
                        "2645a02e0aac1fe69d69755733a9b7621b694bb5b5cde2bbfc94066ed62b9817",
                        "ba982a91d4fc552163cb1c0da03676102d5b7a014304c01f0c77b2b8e888de1c",
                        "9e31407bffa15fefbf5090b149d53959ecdf3f62b1246780238c24501d5ceaf6",
                    ],
                    "merkleRoot": "ccbd66c6f7e8fdab47b3a486f59d28262be857f30d4773f2d5ea47f7761ce0e2",
                    "tweak": "b57bfa183d28eeb6ad688ddaabb265b4a41fbf68e5fed2c72c74de70d5a786f4",
                    "tweakedPubkey": "91b64d5324723a985170e4dc5a0f84c041804f2cd12660fa5dec09fc21783605",
                },
                "expected": {
                    "scriptPubKey": "512091b64d5324723a985170e4dc5a0f84c041804f2cd12660fa5dec09fc21783605",
                    "bip350Address": "bc1pjxmy65eywgafs5tsunw95ruycpqcqnev6ynxp7jaasylcgtcxczs6n332e",
                    "scriptPathControlBlocks": [
                        "c0e0dfe2300b0dd746a3f8674dfd4525623639042569d829c7f0eed9602d263e6fffe578e9ea769027e4f5a3de40732f75a88a6353a09d767ddeb66accef85e553",
                        "c0e0dfe2300b0dd746a3f8674dfd4525623639042569d829c7f0eed9602d263e6f9e31407bffa15fefbf5090b149d53959ecdf3f62b1246780238c24501d5ceaf62645a02e0aac1fe69d69755733a9b7621b694bb5b5cde2bbfc94066ed62b9817",
                        "c0e0dfe2300b0dd746a3f8674dfd4525623639042569d829c7f0eed9602d263e6fba982a91d4fc552163cb1c0da03676102d5b7a014304c01f0c77b2b8e888de1c2645a02e0aac1fe69d69755733a9b7621b694bb5b5cde2bbfc94066ed62b9817",
                    ],
                },
            },
            {
                "given": {
                    "internalPubkey": "55adf4e8967fbd2e29f20ac896e60c3b0f1d5b0efa9d34941b5958c7b0a0312d",
                    "scriptTree": [
                        {
                            "id": 0,
                            "script": "2071981521ad9fc9036687364118fb6ccd2035b96a423c59c5430e98310a11abe2ac",
                            "leafVersion": 192,
                        },
                        [
                            {
                                "id": 1,
                                "script": "20d5094d2dbe9b76e2c245a2b89b6006888952e2faa6a149ae318d69e520617748ac",
                                "leafVersion": 192,
                            },
                            {
                                "id": 2,
                                "script": "20c440b462ad48c7a77f94cd4532d8f2119dcebbd7c9764557e62726419b08ad4cac",
                                "leafVersion": 192,
                            },
                        ],
                    ],
                },
                "intermediary": {
                    "leafHashes": [
                        "f154e8e8e17c31d3462d7132589ed29353c6fafdb884c5a6e04ea938834f0d9d",
                        "737ed1fe30bc42b8022d717b44f0d93516617af64a64753b7a06bf16b26cd711",
                        "d7485025fceb78b9ed667db36ed8b8dc7b1f0b307ac167fa516fe4352b9f4ef7",
                    ],
                    "merkleRoot": "2f6b2c5397b6d68ca18e09a3f05161668ffe93a988582d55c6f07bd5b3329def",
                    "tweak": "6579138e7976dc13b6a92f7bfd5a2fc7684f5ea42419d43368301470f3b74ed9",
                    "tweakedPubkey": "75169f4001aa68f15bbed28b218df1d0a62cbbcf1188c6665110c293c907b831",
                },
                "expected": {
                    "scriptPubKey": "512075169f4001aa68f15bbed28b218df1d0a62cbbcf1188c6665110c293c907b831",
                    "bip350Address": "bc1pw5tf7sqp4f50zka7629jrr036znzew70zxyvvej3zrpf8jg8hqcssyuewe",
                    "scriptPathControlBlocks": [
                        "c155adf4e8967fbd2e29f20ac896e60c3b0f1d5b0efa9d34941b5958c7b0a0312d3cd369a528b326bc9d2133cbd2ac21451acb31681a410434672c8e34fe757e91",
                        "c155adf4e8967fbd2e29f20ac896e60c3b0f1d5b0efa9d34941b5958c7b0a0312dd7485025fceb78b9ed667db36ed8b8dc7b1f0b307ac167fa516fe4352b9f4ef7f154e8e8e17c31d3462d7132589ed29353c6fafdb884c5a6e04ea938834f0d9d",
                        "c155adf4e8967fbd2e29f20ac896e60c3b0f1d5b0efa9d34941b5958c7b0a0312d737ed1fe30bc42b8022d717b44f0d93516617af64a64753b7a06bf16b26cd711f154e8e8e17c31d3462d7132589ed29353c6fafdb884c5a6e04ea938834f0d9d",
                    ],
                },
            },
        ]

        def parse_item(item):
            if isinstance(item, dict):
                tapleaf_version = item["leafVersion"]
                tap_script = TapScript.parse(
                    BytesIO(encode_varstr(bytes.fromhex(item["script"])))
                )
                tap_leaf = TapLeaf(tap_script, tapleaf_version)
                return tap_leaf
            else:
                return TapBranch(parse_item(item[0]), parse_item(item[1]))

        for test in tests:
            point = S256Point.parse_xonly(
                bytes.fromhex(test["given"]["internalPubkey"])
            )
            tap_tree = parse_item(test["given"]["scriptTree"])
            merkle_root = tap_tree.hash()
            merkle_root_want = bytes.fromhex(test["intermediary"]["merkleRoot"])
            self.assertEqual(merkle_root, merkle_root_want)
            raw_tweak = bytes.fromhex(test["intermediary"]["tweak"])
            self.assertEqual(point.tweak(merkle_root), raw_tweak)
            tweak_point_want = S256Point.parse_xonly(
                bytes.fromhex(test["intermediary"]["tweakedPubkey"])
            )
            external_pubkey = point.tweaked_key(merkle_root)
            self.assertEqual(external_pubkey.xonly(), tweak_point_want.xonly())
            stream = BytesIO(
                encode_varstr(bytes.fromhex(test["expected"]["scriptPubKey"]))
            )
            script_pubkey_want = ScriptPubKey.parse(stream)
            self.assertEqual(point.p2tr_script(merkle_root), script_pubkey_want)
            self.assertEqual(
                point.p2tr_address(merkle_root), test["expected"]["bip350Address"]
            )
            control_blocks = test["expected"]["scriptPathControlBlocks"]
            leaf_hashes = test["intermediary"]["leafHashes"]
            for control_block_hex, tap_leaf, leaf_hash in zip(
                control_blocks, tap_tree.leaves(), leaf_hashes
            ):
                self.assertEqual(tap_leaf.hash(), bytes.fromhex(leaf_hash))
                control_block_raw = bytes.fromhex(control_block_hex)
                control_block_want = ControlBlock.parse(control_block_raw)
                control_block = tap_tree.control_block(point, tap_leaf)
                self.assertEqual(control_block, control_block_want)
                self.assertEqual(
                    tap_leaf.tapleaf_version, control_block.tapleaf_version
                )
                self.assertEqual(control_block.serialize(), control_block_raw)
                self.assertEqual(control_block.internal_pubkey, point)
                self.assertEqual(
                    control_block.merkle_root(tap_leaf.tap_script), merkle_root
                )
                self.assertEqual(
                    control_block.internal_pubkey.tweak(merkle_root), raw_tweak
                )

    def test_p2tr_spending(self):
        test = {
            "given": {
                "rawUnsignedTx": "02000000097de20cbff686da83a54981d2b9bab3586f4ca7e48f57f5b55963115f3b334e9c010000000000000000d7b7cab57b1393ace2d064f4d4a2cb8af6def61273e127517d44759b6dafdd990000000000fffffffff8e1f583384333689228c5d28eac13366be082dc57441760d957275419a418420000000000fffffffff0689180aa63b30cb162a73c6d2a38b7eeda2a83ece74310fda0843ad604853b0100000000feffffffaa5202bdf6d8ccd2ee0f0202afbbb7461d9264a25e5bfd3c5a52ee1239e0ba6c0000000000feffffff956149bdc66faa968eb2be2d2faa29718acbfe3941215893a2a3446d32acd050000000000000000000e664b9773b88c09c32cb70a2a3e4da0ced63b7ba3b22f848531bbb1d5d5f4c94010000000000000000e9aa6b8e6c9de67619e6a3924ae25696bb7b694bb677a632a74ef7eadfd4eabf0000000000ffffffffa778eb6a263dc090464cd125c466b5a99667720b1c110468831d058aa1b82af10100000000ffffffff0200ca9a3b000000001976a91406afd46bcdfd22ef94ac122aa11f241244a37ecc88ac807840cb0000000020ac9a87f5594be208f8532db38cff670c450ed2fea8fcdefcc9a663f78bab962b0065cd1d",
                "utxosSpent": [
                    {
                        "scriptPubKey": "512053a1f6e454df1aa2776a2814a721372d6258050de330b3c6d10ee8f4e0dda343",
                        "amountSats": 420000000,
                    },
                    {
                        "scriptPubKey": "5120147c9c57132f6e7ecddba9800bb0c4449251c92a1e60371ee77557b6620f3ea3",
                        "amountSats": 462000000,
                    },
                    {
                        "scriptPubKey": "76a914751e76e8199196d454941c45d1b3a323f1433bd688ac",
                        "amountSats": 294000000,
                    },
                    {
                        "scriptPubKey": "5120e4d810fd50586274face62b8a807eb9719cef49c04177cc6b76a9a4251d5450e",
                        "amountSats": 504000000,
                    },
                    {
                        "scriptPubKey": "512091b64d5324723a985170e4dc5a0f84c041804f2cd12660fa5dec09fc21783605",
                        "amountSats": 630000000,
                    },
                    {
                        "scriptPubKey": "00147dd65592d0ab2fe0d0257d571abf032cd9db93dc",
                        "amountSats": 378000000,
                    },
                    {
                        "scriptPubKey": "512075169f4001aa68f15bbed28b218df1d0a62cbbcf1188c6665110c293c907b831",
                        "amountSats": 672000000,
                    },
                    {
                        "scriptPubKey": "5120712447206d7a5238acc7ff53fbe94a3b64539ad291c7cdbc490b7577e4b17df5",
                        "amountSats": 546000000,
                    },
                    {
                        "scriptPubKey": "512077e30a5522dd9f894c3f8b8bd4c4b2cf82ca7da8a3ea6a239655c39c050ab220",
                        "amountSats": 588000000,
                    },
                ],
            },
            "intermediary": {
                "hashAmounts": "58a6964a4f5f8f0b642ded0a8a553be7622a719da71d1f5befcefcdee8e0fde6",
                "hashOutputs": "a2e6dab7c1f0dcd297c8d61647fd17d821541ea69c3cc37dcbad7f90d4eb4bc5",
                "hashPrevouts": "e3b33bb4ef3a52ad1fffb555c0d82828eb22737036eaeb02a235d82b909c4c3f",
                "hashScriptPubkeys": "23ad0f61ad2bca5ba6a7693f50fce988e17c3780bf2b1e720cfbb38fbdd52e21",
                "hashSequences": "18959c7221ab5ce9e26c3cd67b22c24f8baa54bac281d8e6b05e400e6c3a957e",
            },
            "inputSpending": [
                {
                    "given": {
                        "txinIndex": 0,
                        "internalPrivkey": "6b973d88838f27366ed61c9ad6367663045cb456e28335c109e30717ae0c6baa",
                        "merkleRoot": None,
                        "hashType": 3,
                    },
                    "intermediary": {
                        "internalPubkey": "d6889cb081036e0faefa3a35157ad71086b123b2b144b649798b494c300a961d",
                        "tweak": "b86e7be8f39bab32a6f2c0443abbc210f0edac0e2c53d501b36b64437d9c6c70",
                        "tweakedPrivkey": "2405b971772ad26915c8dcdf10f238753a9b837e5f8e6a86fd7c0cce5b7296d9",
                        "sigMsg": "0003020000000065cd1de3b33bb4ef3a52ad1fffb555c0d82828eb22737036eaeb02a235d82b909c4c3f58a6964a4f5f8f0b642ded0a8a553be7622a719da71d1f5befcefcdee8e0fde623ad0f61ad2bca5ba6a7693f50fce988e17c3780bf2b1e720cfbb38fbdd52e2118959c7221ab5ce9e26c3cd67b22c24f8baa54bac281d8e6b05e400e6c3a957e0000000000d0418f0e9a36245b9a50ec87f8bf5be5bcae434337b87139c3a5b1f56e33cba0",
                        "precomputedUsed": [
                            "hashAmounts",
                            "hashPrevouts",
                            "hashScriptPubkeys",
                            "hashSequences",
                        ],
                        "sigHash": "2514a6272f85cfa0f45eb907fcb0d121b808ed37c6ea160a5a9046ed5526d555",
                    },
                    "expected": {
                        "witness": [
                            "ed7c1647cb97379e76892be0cacff57ec4a7102aa24296ca39af7541246d8ff14d38958d4cc1e2e478e4d4a764bbfd835b16d4e314b72937b29833060b87276c03"
                        ]
                    },
                },
                {
                    "given": {
                        "txinIndex": 1,
                        "internalPrivkey": "1e4da49f6aaf4e5cd175fe08a32bb5cb4863d963921255f33d3bc31e1343907f",
                        "merkleRoot": "5b75adecf53548f3ec6ad7d78383bf84cc57b55a3127c72b9a2481752dd88b21",
                        "hashType": 131,
                    },
                    "intermediary": {
                        "internalPubkey": "187791b6f712a8ea41c8ecdd0ee77fab3e85263b37e1ec18a3651926b3a6cf27",
                        "tweak": "cbd8679ba636c1110ea247542cfbd964131a6be84f873f7f3b62a777528ed001",
                        "tweakedPrivkey": "ea260c3b10e60f6de018455cd0278f2f5b7e454be1999572789e6a9565d26080",
                        "sigMsg": "0083020000000065cd1d00d7b7cab57b1393ace2d064f4d4a2cb8af6def61273e127517d44759b6dafdd9900000000808f891b00000000225120147c9c57132f6e7ecddba9800bb0c4449251c92a1e60371ee77557b6620f3ea3ffffffffffcef8fb4ca7efc5433f591ecfc57391811ce1e186a3793024def5c884cba51d",
                        "precomputedUsed": [],
                        "sigHash": "325a644af47e8a5a2591cda0ab0723978537318f10e6a63d4eed783b96a71a4d",
                    },
                    "expected": {
                        "witness": [
                            "052aedffc554b41f52b521071793a6b88d6dbca9dba94cf34c83696de0c1ec35ca9c5ed4ab28059bd606a4f3a657eec0bb96661d42921b5f50a95ad33675b54f83"
                        ]
                    },
                },
                {
                    "given": {
                        "txinIndex": 3,
                        "internalPrivkey": "d3c7af07da2d54f7a7735d3d0fc4f0a73164db638b2f2f7c43f711f6d4aa7e64",
                        "merkleRoot": "c525714a7f49c28aedbbba78c005931a81c234b2f6c99a73e4d06082adc8bf2b",
                        "hashType": 1,
                    },
                    "intermediary": {
                        "internalPubkey": "93478e9488f956df2396be2ce6c5cced75f900dfa18e7dabd2428aae78451820",
                        "tweak": "6af9e28dbf9d6aaf027696e2598a5b3d056f5fd2355a7fd5a37a0e5008132d30",
                        "tweakedPrivkey": "97323385e57015b75b0339a549c56a948eb961555973f0951f555ae6039ef00d",
                        "sigMsg": "0001020000000065cd1de3b33bb4ef3a52ad1fffb555c0d82828eb22737036eaeb02a235d82b909c4c3f58a6964a4f5f8f0b642ded0a8a553be7622a719da71d1f5befcefcdee8e0fde623ad0f61ad2bca5ba6a7693f50fce988e17c3780bf2b1e720cfbb38fbdd52e2118959c7221ab5ce9e26c3cd67b22c24f8baa54bac281d8e6b05e400e6c3a957ea2e6dab7c1f0dcd297c8d61647fd17d821541ea69c3cc37dcbad7f90d4eb4bc50003000000",
                        "precomputedUsed": [
                            "hashAmounts",
                            "hashOutputs",
                            "hashPrevouts",
                            "hashScriptPubkeys",
                            "hashSequences",
                        ],
                        "sigHash": "bf013ea93474aa67815b1b6cc441d23b64fa310911d991e713cd34c7f5d46669",
                    },
                    "expected": {
                        "witness": [
                            "ff45f742a876139946a149ab4d9185574b98dc919d2eb6754f8abaa59d18b025637a3aa043b91817739554f4ed2026cf8022dbd83e351ce1fabc272841d2510a01"
                        ]
                    },
                },
                {
                    "given": {
                        "txinIndex": 4,
                        "internalPrivkey": "f36bb07a11e469ce941d16b63b11b9b9120a84d9d87cff2c84a8d4affb438f4e",
                        "merkleRoot": "ccbd66c6f7e8fdab47b3a486f59d28262be857f30d4773f2d5ea47f7761ce0e2",
                        "hashType": 0,
                    },
                    "intermediary": {
                        "internalPubkey": "e0dfe2300b0dd746a3f8674dfd4525623639042569d829c7f0eed9602d263e6f",
                        "tweak": "b57bfa183d28eeb6ad688ddaabb265b4a41fbf68e5fed2c72c74de70d5a786f4",
                        "tweakedPrivkey": "a8e7aa924f0d58854185a490e6c41f6efb7b675c0f3331b7f14b549400b4d501",
                        "sigMsg": "0000020000000065cd1de3b33bb4ef3a52ad1fffb555c0d82828eb22737036eaeb02a235d82b909c4c3f58a6964a4f5f8f0b642ded0a8a553be7622a719da71d1f5befcefcdee8e0fde623ad0f61ad2bca5ba6a7693f50fce988e17c3780bf2b1e720cfbb38fbdd52e2118959c7221ab5ce9e26c3cd67b22c24f8baa54bac281d8e6b05e400e6c3a957ea2e6dab7c1f0dcd297c8d61647fd17d821541ea69c3cc37dcbad7f90d4eb4bc50004000000",
                        "precomputedUsed": [
                            "hashAmounts",
                            "hashOutputs",
                            "hashPrevouts",
                            "hashScriptPubkeys",
                            "hashSequences",
                        ],
                        "sigHash": "4f900a0bae3f1446fd48490c2958b5a023228f01661cda3496a11da502a7f7ef",
                    },
                    "expected": {
                        "witness": [
                            "b4010dd48a617db09926f729e79c33ae0b4e94b79f04a1ae93ede6315eb3669de185a17d2b0ac9ee09fd4c64b678a0b61a0a86fa888a273c8511be83bfd6810f"
                        ]
                    },
                },
                {
                    "given": {
                        "txinIndex": 6,
                        "internalPrivkey": "415cfe9c15d9cea27d8104d5517c06e9de48e2f986b695e4f5ffebf230e725d8",
                        "merkleRoot": "2f6b2c5397b6d68ca18e09a3f05161668ffe93a988582d55c6f07bd5b3329def",
                        "hashType": 2,
                    },
                    "intermediary": {
                        "internalPubkey": "55adf4e8967fbd2e29f20ac896e60c3b0f1d5b0efa9d34941b5958c7b0a0312d",
                        "tweak": "6579138e7976dc13b6a92f7bfd5a2fc7684f5ea42419d43368301470f3b74ed9",
                        "tweakedPrivkey": "241c14f2639d0d7139282aa6abde28dd8a067baa9d633e4e7230287ec2d02901",
                        "sigMsg": "0002020000000065cd1de3b33bb4ef3a52ad1fffb555c0d82828eb22737036eaeb02a235d82b909c4c3f58a6964a4f5f8f0b642ded0a8a553be7622a719da71d1f5befcefcdee8e0fde623ad0f61ad2bca5ba6a7693f50fce988e17c3780bf2b1e720cfbb38fbdd52e2118959c7221ab5ce9e26c3cd67b22c24f8baa54bac281d8e6b05e400e6c3a957e0006000000",
                        "precomputedUsed": [
                            "hashAmounts",
                            "hashPrevouts",
                            "hashScriptPubkeys",
                            "hashSequences",
                        ],
                        "sigHash": "15f25c298eb5cdc7eb1d638dd2d45c97c4c59dcaec6679cfc16ad84f30876b85",
                    },
                    "expected": {
                        "witness": [
                            "a3785919a2ce3c4ce26f298c3d51619bc474ae24014bcdd31328cd8cfbab2eff3395fa0a16fe5f486d12f22a9cedded5ae74feb4bbe5351346508c5405bcfee002"
                        ]
                    },
                },
                {
                    "given": {
                        "txinIndex": 7,
                        "internalPrivkey": "c7b0e81f0a9a0b0499e112279d718cca98e79a12e2f137c72ae5b213aad0d103",
                        "merkleRoot": "6c2dc106ab816b73f9d07e3cd1ef2c8c1256f519748e0813e4edd2405d277bef",
                        "hashType": 130,
                    },
                    "intermediary": {
                        "internalPubkey": "ee4fe085983462a184015d1f782d6a5f8b9c2b60130aff050ce221ecf3786592",
                        "tweak": "9e0517edc8259bb3359255400b23ca9507f2a91cd1e4250ba068b4eafceba4a9",
                        "tweakedPrivkey": "65b6000cd2bfa6b7cf736767a8955760e62b6649058cbc970b7c0871d786346b",
                        "sigMsg": "0082020000000065cd1d00e9aa6b8e6c9de67619e6a3924ae25696bb7b694bb677a632a74ef7eadfd4eabf00000000804c8b2000000000225120712447206d7a5238acc7ff53fbe94a3b64539ad291c7cdbc490b7577e4b17df5ffffffff",
                        "precomputedUsed": [],
                        "sigHash": "cd292de50313804dabe4685e83f923d2969577191a3e1d2882220dca88cbeb10",
                    },
                    "expected": {
                        "witness": [
                            "ea0c6ba90763c2d3a296ad82ba45881abb4f426b3f87af162dd24d5109edc1cdd11915095ba47c3a9963dc1e6c432939872bc49212fe34c632cd3ab9fed429c482"
                        ]
                    },
                },
                {
                    "given": {
                        "txinIndex": 8,
                        "internalPrivkey": "77863416be0d0665e517e1c375fd6f75839544eca553675ef7fdf4949518ebaa",
                        "merkleRoot": "ab179431c28d3b68fb798957faf5497d69c883c6fb1e1cd9f81483d87bac90cc",
                        "hashType": 129,
                    },
                    "intermediary": {
                        "internalPubkey": "f9f400803e683727b14f463836e1e78e1c64417638aa066919291a225f0e8dd8",
                        "tweak": "639f0281b7ac49e742cd25b7f188657626da1ad169209078e2761cefd91fd65e",
                        "tweakedPrivkey": "ec18ce6af99f43815db543f47b8af5ff5df3b2cb7315c955aa4a86e8143d2bf5",
                        "sigMsg": "0081020000000065cd1da2e6dab7c1f0dcd297c8d61647fd17d821541ea69c3cc37dcbad7f90d4eb4bc500a778eb6a263dc090464cd125c466b5a99667720b1c110468831d058aa1b82af101000000002b0c230000000022512077e30a5522dd9f894c3f8b8bd4c4b2cf82ca7da8a3ea6a239655c39c050ab220ffffffff",
                        "precomputedUsed": ["hashOutputs"],
                        "sigHash": "cccb739eca6c13a8a89e6e5cd317ffe55669bbda23f2fd37b0f18755e008edd2",
                    },
                    "expected": {
                        "witness": [
                            "bbc9584a11074e83bc8c6759ec55401f0ae7b03ef290c3139814f545b58a9f8127258000874f44bc46db7646322107d4d86aec8e73b8719a61fff761d75b5dd981"
                        ]
                    },
                },
            ],
            "auxiliary": {
                "fullySignedTx": "020000000001097de20cbff686da83a54981d2b9bab3586f4ca7e48f57f5b55963115f3b334e9c010000000000000000d7b7cab57b1393ace2d064f4d4a2cb8af6def61273e127517d44759b6dafdd990000000000fffffffff8e1f583384333689228c5d28eac13366be082dc57441760d957275419a41842000000006b4830450221008f3b8f8f0537c420654d2283673a761b7ee2ea3c130753103e08ce79201cf32a022079e7ab904a1980ef1c5890b648c8783f4d10103dd62f740d13daa79e298d50c201210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798fffffffff0689180aa63b30cb162a73c6d2a38b7eeda2a83ece74310fda0843ad604853b0100000000feffffffaa5202bdf6d8ccd2ee0f0202afbbb7461d9264a25e5bfd3c5a52ee1239e0ba6c0000000000feffffff956149bdc66faa968eb2be2d2faa29718acbfe3941215893a2a3446d32acd050000000000000000000e664b9773b88c09c32cb70a2a3e4da0ced63b7ba3b22f848531bbb1d5d5f4c94010000000000000000e9aa6b8e6c9de67619e6a3924ae25696bb7b694bb677a632a74ef7eadfd4eabf0000000000ffffffffa778eb6a263dc090464cd125c466b5a99667720b1c110468831d058aa1b82af10100000000ffffffff0200ca9a3b000000001976a91406afd46bcdfd22ef94ac122aa11f241244a37ecc88ac807840cb0000000020ac9a87f5594be208f8532db38cff670c450ed2fea8fcdefcc9a663f78bab962b0141ed7c1647cb97379e76892be0cacff57ec4a7102aa24296ca39af7541246d8ff14d38958d4cc1e2e478e4d4a764bbfd835b16d4e314b72937b29833060b87276c030141052aedffc554b41f52b521071793a6b88d6dbca9dba94cf34c83696de0c1ec35ca9c5ed4ab28059bd606a4f3a657eec0bb96661d42921b5f50a95ad33675b54f83000141ff45f742a876139946a149ab4d9185574b98dc919d2eb6754f8abaa59d18b025637a3aa043b91817739554f4ed2026cf8022dbd83e351ce1fabc272841d2510a010140b4010dd48a617db09926f729e79c33ae0b4e94b79f04a1ae93ede6315eb3669de185a17d2b0ac9ee09fd4c64b678a0b61a0a86fa888a273c8511be83bfd6810f0247304402202b795e4de72646d76eab3f0ab27dfa30b810e856ff3a46c9a702df53bb0d8cc302203ccc4d822edab5f35caddb10af1be93583526ccfbade4b4ead350781e2f8adcd012102f9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f90141a3785919a2ce3c4ce26f298c3d51619bc474ae24014bcdd31328cd8cfbab2eff3395fa0a16fe5f486d12f22a9cedded5ae74feb4bbe5351346508c5405bcfee0020141ea0c6ba90763c2d3a296ad82ba45881abb4f426b3f87af162dd24d5109edc1cdd11915095ba47c3a9963dc1e6c432939872bc49212fe34c632cd3ab9fed429c4820141bbc9584a11074e83bc8c6759ec55401f0ae7b03ef290c3139814f545b58a9f8127258000874f44bc46db7646322107d4d86aec8e73b8719a61fff761d75b5dd9810065cd1d"
            },
        }
        hex_tx = test["given"]["rawUnsignedTx"]
        tx_obj = Tx.parse(BytesIO(bytes.fromhex(hex_tx)))
        self.maxDiff = None
        self.assertEqual(tx_obj.serialize().hex(), hex_tx)
        tx_obj.segwit = True
        for tx_in, utxo in zip(tx_obj.tx_ins, test["given"]["utxosSpent"]):
            tx_in._value = utxo["amountSats"]
            tx_in._script_pubkey = Script.parse(
                BytesIO(encode_varstr(bytes.fromhex(utxo["scriptPubKey"])))
            )
        shas = test["intermediary"]
        self.assertEqual(tx_obj.sha_amounts().hex(), shas["hashAmounts"])
        self.assertEqual(tx_obj.sha_outputs().hex(), shas["hashOutputs"])
        self.assertEqual(tx_obj.sha_prevouts().hex(), shas["hashPrevouts"])
        self.assertEqual(tx_obj.sha_script_pubkeys().hex(), shas["hashScriptPubkeys"])
        self.assertEqual(tx_obj.sha_sequences().hex(), shas["hashSequences"])
        fully_signed = test["auxiliary"]["fullySignedTx"]
        signed_tx = Tx.parse(BytesIO(bytes.fromhex(fully_signed)))
        for input_data in test["inputSpending"]:
            i = input_data["given"]["txinIndex"]
            secret = big_endian_to_int(
                bytes.fromhex(input_data["given"]["internalPrivkey"])
            )
            tx_in = tx_obj.tx_ins[i]
            private_key = PrivateKey(secret)
            pubkey = private_key.point
            hash_type = input_data["given"]["hashType"]
            self.assertEqual(
                pubkey.xonly().hex(), input_data["intermediary"]["internalPubkey"]
            )
            mr_hex = input_data["given"]["merkleRoot"]
            if mr_hex is None:
                merkle_root = b""
            else:
                merkle_root = bytes.fromhex(mr_hex)
            tweak_want = bytes.fromhex(input_data["intermediary"]["tweak"])
            self.assertEqual(pubkey.tweak(merkle_root), tweak_want)
            tweaked_private_key = private_key.tweaked_key(merkle_root)
            tweaked_want = big_endian_to_int(
                bytes.fromhex(input_data["intermediary"]["tweakedPrivkey"])
            )
            self.assertEqual(tweaked_private_key.secret, tweaked_want)
            sig_hash_want = input_data["intermediary"]["sigHash"]
            self.assertEqual(
                tx_obj.sig_hash_bip341(i, hash_type=hash_type).hex(), sig_hash_want
            )
            tx_obj.sign_input(i, tweaked_private_key, hash_type=hash_type)
            for j, witness_want in enumerate(input_data["expected"]["witness"]):
                self.assertEqual(tx_in.witness[j].hex(), witness_want)
        # the two we can't sign
        for i in (2, 5):
            signed_tx.tx_ins[i].script_sig = Script()
            signed_tx.tx_ins[i].witness = Witness()
        self.assertEqual(tx_obj.serialize(), signed_tx.serialize())
