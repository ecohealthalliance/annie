#!/usr/bin/env python
"""
Tests our ability to annotate sentences with numerical
instances of infections, hospitalizations and deaths.
"""

import sys
import unittest
import test_utils

sys.path = ['./'] + sys.path

from annotator.annotator import AnnoDoc
from annotator.count_annotator import CountAnnotator

class TestCountAnnotator(unittest.TestCase):

    def setUp(self):
        self.annotator = CountAnnotator()

    def test_no_counts(self):
        doc = AnnoDoc("Fever")
        doc.add_tier(self.annotator)

    def test_false_positive_counts(self):
        examples = [
            "Measles - Democratic Republic of the Congo (Katanga) 2007.1775",
            "Meningitis - Democratic Republic of Congo [02] 970814010223"
        ]
        for example in examples:
            doc = AnnoDoc(example)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts']), 0)

    def test_verb_counts(self):
        examples = [
            ("it brings the number of cases reported to 28 in Jeddah since 27 Mar 2014", 28),
            ("There have been nine hundred ninety-nine reported cases.", 999)
        ]
        for example, actual_count in examples:
            doc = AnnoDoc(example)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts']), 1)
            test_utils.assertHasProps(
                doc.tiers['counts'].spans[0].metadata, {
                    'count': actual_count,
                    'attributes': ['case']
                })

    def test_death_counts(self):
        examples = [("The number of deaths is 30", 30),
                    # Also test unicode
                    (u"The number of deaths is 30", 30),
                    ("Nine patients died last week", 9)]
        for example, actual_count in examples:
            doc = AnnoDoc(example)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts']), 1)
            test_utils.assertHasProps(
                doc.tiers['counts'].spans[0].metadata, {
                    'count': actual_count,
                    'attributes': ['case', 'death']
                })

    def test_offsets(self):
        doc = AnnoDoc("The ministry of health reports seventy five new patients were admitted")
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['counts']), 1)
        self.assertEqual(doc.tiers['counts'].spans[0].start, 31)
        self.assertEqual(doc.tiers['counts'].spans[0].end, 56)
        test_utils.assertHasProps(
            doc.tiers['counts'].spans[0].metadata, {
                'count' : 75
            }
        )

    def test_written_numbers(self):
        doc = AnnoDoc("""
            Two hundred and twenty two patients were admitted to hospitals.
            In total, there were five million three hundred and forty eight thousand new cases last year.""")
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['counts']), 2)
        test_utils.assertHasProps(
            doc.tiers['counts'].spans[0].metadata, {
                'count': 222
            }
        )
        test_utils.assertHasProps(
            doc.tiers['counts'].spans[1].metadata, {
                'count': 5348000
            }
        )
    def test_hospitalization_counts1(self):
        examples = [("33 were hospitalized", 33),
                    ("222 were admitted to hospitals with symptoms of diarrhea", 222)]
        for example, actual_count in examples:
            doc = AnnoDoc(example)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts']), 1)
            test_utils.assertHasProps(
                doc.tiers['counts'].spans[0].metadata, {
                    'count': actual_count,
                    'attributes': ['hospitalization']
                })

    def test_colon_delimited_counts(self):
        doc = AnnoDoc("Deaths: 2")
        doc.add_tier(self.annotator)

        self.assertEqual(len(doc.tiers['counts']), 1)
        self.assertEqual(doc.tiers['counts'].spans[0].start, 0)
        self.assertEqual(doc.tiers['counts'].spans[0].end, 9)
        test_utils.assertHasProps(
            doc.tiers['counts'].spans[0].metadata, {
                'count': 2
            })

    def test_age_elimination(self):
        doc = AnnoDoc("1200 children under the age of 5 are afflicted with a mystery illness")
        doc.add_tier(self.annotator)
        test_utils.assertHasProps(
            doc.tiers['counts'].spans[0].metadata, {
                'count' : 1200
            }
        )
        self.assertEqual(len(doc.tiers['counts'].spans), 1)

    def test_raw_counts(self):
        doc = AnnoDoc("There are 5 new ones.")
        doc.add_tier(self.annotator)
        test_utils.assertHasProps(
            doc.tiers['counts'].spans[0].metadata, {
                'count' : 5,
                'attributes': ['incremental']
            }
        )
        self.assertEqual(len(doc.tiers['counts'].spans), 1)

    def test_complex(self):
        examples = [
            ("These 2 new cases bring to 4 the number stricken in California this year [2012].", [
                {'count': 2, 'attributes': ['case', 'incremental']},
                {'count': 4, 'attributes': ['case']},
            ]),
            ("Two patients died out of four patients.", [
                {'count': 2, 'attributes': ['case', 'death']},
                {'count': 4, 'attributes': ['case']},
            ]),
        ]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)

    def test_cumulative(self):
        examples = [
            ("In total nationwide, 613 cases of the disease have been reported as of 2 Jul 2014, with 63 deaths", [
                {'count': 613, 'attributes': ['case', 'cumulative']},
                {'count': 63, 'attributes': ['case', 'death']}
            ]), 
            ("it has already claimed about 455 lives in Guinea", [
                {'count': 455, 'attributes': ['approximate', 'case', 'cumulative', 'death']}
            ])
        ]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)

    def test_attributes(self):
        examples= [
            ("There have been 12 reported cases in Colorado. " +
            "There was one suspected case of bird flu in the country.", [
                { 'count': 12, 'attributes': ['case'] },
                { 'count': 1, 'attributes': ['case', 'suspected'] }
            ]),
            ("The average number of cases reported annually is 600", [
                { 'count': 600, 'attributes': ['annual', 'average', 'case'] }
            ])
        ]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)

    def test_misc(self):
        examples= [
            ("""How many cases occured with 3.2 miles of Katanga Province?
                Three fatalities have been reported.""", [{'count': 3}])
        ]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)

    def test_distance_and_percentage_filtering(self):
        examples= [
            ("48 percent of the cases occured in Seattle", []),
            ("28 kilometers away [17.4 miles]", [])
        ]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)

    def test_tokenization_edge_cases(self):
        """
        These examples triggered some bugs with word token alignment in the past.
        """
        examples= [
            ("These numbers include laboratory-confirmed, probable, and suspect cases and deaths of EVD.", []),
            ("""22 new cases of EVD, including 14 deaths, were reported as follows:
        Guinea, 3 new cases and 5 deaths; Liberia, 8 new cases with 7 deaths; and Sierra Leone 11 new cases and 2 deaths.
        """, [{'count':22},{'count':14},{'count':3},{'count':5},{'count':8},{'count':7},{'count':11},{'count':2}])]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)

    def test_internals(self):
        from annotator.count_annotator import search_spans_for_regex
        import annotator.result_aggregators as ra
        doc = AnnoDoc("Deaths: 2")
        doc.add_tier(self.annotator)
        ra.follows([
            search_spans_for_regex('deaths(\s?:)?', doc.tiers['spacy.tokens'].spans),
            search_spans_for_regex('\d+', doc.tiers['spacy.tokens'].spans)])

    def test_full_article(self):
        """
        Tests a full length article
        """

        example = """CYTAUXZOONOSIS, FELINE - USA: (OKLAHOMA)
            ****************************************
            A ProMED-mail post
            http://www.promedmail.org
            ProMED-mail is a program of the
            International Society for Infectious Diseases
            http://www.isid.org

            Date: Sun 23 Apr 2017
            Source: Norman Transcript [edited]
            http://www.normantranscript.com/news/local_news/fatal-bobcat-fever-is-tick-borne-nearby/article_ec1ab309-17a6-510d-93dd-27a1c678a128.html

            A deadly assailant may be lurking in your backyard. Rural Norman residents mourn companion pets. 

            Ticks, and in particular the Lone Star tick, carry many diseases which can be hazardous to pets and humans. Few diseases are more deadly, however, than Bobcat fever, or _Cytauxzoon felis_, which infects cats and has a very high mortality rate.

            "The Lone Star tick has been carrying this disease for a long time, and cats have been getting it for a long time," said Dr Laura Nafe, a veterinarian at Oklahoma State University. "The Lone Star Tick is really common in Oklahoma and it carries a lot of diseases that affect cats and dogs."

            Rural Norman resident BT knows all too well how deadly this disease can be. Her beloved cat Paw Paws succumbed to Bobcat fever recently and her veterinarian told her there have been several other deadly cases since Paw Paws' demise.

            "It was just so sudden, I didn't know about it prior to this," BT said. "He couldn't walk right and had a little blood from his nose. We took him to the vet, but he died. They put in a lot of effort to make sure that's what it was and to get the medication."

            Unfortunately, it was too late for Paw Paws, who had one dose of the medication but died anyway. BT had been using a topical flea and tick preventative on Paw Paws, but it apparently didn't provide enough prevention, she said.

            Bobcats aren't affected by the disease, but they are carriers, making wooded areas like rural Norman particularly high risk. Bobcat fever doesn't affect humans or dogs, though many other tick-borne diseases do. Tick prevention is a good investment for the health of all family members.

            "We see a lot of cases in Oklahoma," Nafe said. "Between now and early June is the peak time, but every single month of the year, a case has been reported in Oklahoma. No tick preventative is 100 percent, but the best treatment for this disease is to not let your cat be exposed to it."

            While rural kitties are more likely to contract the disease, city cats are not immune. "Even city areas of Oklahoma may still have wooded areas that have bobcats," Nafe said. "I've yet to see an indoor only house cat get it."

            Ticks must feed on a bobcat, drop off and then be picked up by a cat, so the rate of infection will be much higher for cats who live around Lake Thunderbird where bobcats are prevalent.

            "It's deadly for our kitty cats. I think people need to know about it," BT said. "Paw Paws was a beautiful cat. He had been abandoned. His little paws were smashed, but he grew up healthy. He was in his prime, doing great, then this hit him."

            The female Lone Star tick has a whitish spot on its back, but Nafe said other ticks carry diseases as well. "The majority of owners don't see a tick on their cat," Nafe said.

            If you can't keep your cat indoors, Nafe suggests aggressive tick prevention. A Soresto collar lasts about 8 months. "[Soresto collars] are made to break if a cat hangs itself," Nafe said. "That's a good idea for cats that you can't catch monthly to give them a flea preventative."

            If you live in an area with bobcats where lots of cats have died, you can also apply a topical preventative with the collar, Nafe said, but check with your veterinarian to make sure using the combination is safe for your cat.

            "I think we've had 5 [cat deaths from bobcat fever] this year [2017]," said Dr Karla Denton, of Sooner Veterinary Hospital. "It's in the rural areas and especially if anyone's seen a bobcat or anyone close to a lake."

            A Ward 5 resident herself, [D] has several feral barn cats. "The beginning of every year I trap them and put the Soresto collars on them," [D] said. "Those work great if they keep the collar on." [D] believes she's lost a couple of cats to Bobcat fever over the years, and her house cat doesn't go outside.
            "It's a USD 56 collar that lasts 8 months," Denton said. [D] said vet clinics like Sooner Veterinary Hospital, often have rebates available for the Soresto collar.

            Prevention is more effective than available cures.

            "There is not a vaccine for the disease right now," Nafe said. "The best recommendation for treatment is a combination of 2 drugs, one is an anti-malarial and the other is an anti microbial."

            Both have human applications, but unless a veterinarian has the anti-malarial on the shelf, she has to buy the whole bottle, and once opened it expires after a year.

            "There are compounding pharmacies that will sell you specifically what you need, the problem is you need it fast because you don't want to delay treatment 1-2 days waiting for that treatment to be mailed," Nafe said.
            Even with treatment, a cat might not survive. One study found a 60 percent survival rate but Nafe said she doesn't think survival is that high in Oklahoma.

            "I think we see a more virulent strain of it here," she said. "There are cats that can live through this disease. They may need oxygen and IV fluids. They're very sick, and they're very sick suddenly."

            BT said nothing can bring Paw Paws back, but she wanted to share the information to save others the heartache of losing a feline friend.

            [Byline: Joy Hampton]

            --
            Communicated by:
            ProMED-mail from HealthMap Alerts
            <promed@promedmail.org>

            [Although this disease can and does appear anywhere, especially considering our mobile society, it has most frequently been diagnosed in Missouri, Arkansas, Florida, Georgia, Louisiana, Mississippi, Oklahoma, Texas, Kentucky, Kansas, Tennessee, North Carolina, South Carolina, Nebraska, Iowa, and Virginia. There are also reports of Illinois and California having diagnosis of _Cytauxzoon_ spp.

            Cytauxzoonosis is an emerging, life-threatening infectious disease of domestic cats (_Felis catus_) caused by the tick-transmitted protozoan parasite _Cytauxzoon felis_. _Cytauxzoon_ spp are apicomplexan parasites within the family Theileriidae along with their closest relatives of _Theileria_ spp. _C. felis_ is transmitted to domestic cats by the lone star tick (_Amblyomma americanum_). The natural host for _C. felis_ is the bobcat (_Lynx rufus_); reservoir hosts of the parasite include bobcats and domestic cats that survive infection.

            _C. felis_ is transmitted by the lone star tick, _A. americanum_. Cytauxzoonosis is typically diagnosed during April through September, which correlates with climate-dependent seasonal tick activity. Cats living near heavily wooded, low-density residential areas particularly close to natural or unmanaged habitats where both ticks and bobcats may be in close proximity are at highest risk of infection. In some cases this may include areas designated as parks, or hiking trails. Experimental infections have been induced with parenteral injection of tissue homogenates from acutely infected cats. However, infection was not induced when these tissues were administered intragastrically or when noninfected cats were housed together with infected cats in the absence of arthropod vectors, suggesting that oral and "cat-to-cat" transmission does not occur. One recent study failed to document perinatal transmission of _C. felis_ from 2 chronically infected dams to 14 healthy kittens, suggesting that vertical transmission may not occur commonly, if at all.

            Onset of clinical signs for cats infected with _C. felis_ usually occurs 5-14 days (about 10 on average) after infection by tick transmission. Nonspecific signs such as depression, lethargy, and anorexia are the most common presenting problems. Pyrexia and dehydration are the most common findings on physical examination; body temperature, which increases gradually, can be as high as 106 deg F (41 deg C). Other findings include icterus, lymphadenomegaly, and hepatosplenomegaly. In extremis, cats are often hypothermic, dyspneic, and vocalize as if in pain. Without treatment, death typically occurs within 2-3 days after peak in temperature. At necropsy, splenomegaly, hepatomegaly, enlarged lymph nodes, and renal edema are usually seen. The lungs show extensive edema and congestion with petechial hemorrhage on serosal surfaces and throughout the interstitium. There is progressive venous distention, especially of the mesenteric and renal veins and the posterior vena cava. Hydropericardium is often seen with petechial hemorrhage of the epicardium.

            When 1st described, mortality of _C. felis_ infection was reported to be nearly 100 percent. A study of _C. felis_ in northwestern Arkansas and northeastern Oklahoma indicated survival of natural infection in 18 cats with and without treatment; these cats seemed "less sick" initially, did not have temperatures greater than 106 deg F (41 deg C), and never became hypothermic. Similar sporadic reports in other areas exist. Some hypotheses for survival in these cats have included the following: 1) an atypical route of infection, 2) innate immunity in certain cats, 3) increased detection of carriers, 4) decreased virulence with strain attenuation or occurrence of a new strain, 5) dose of infectious inoculum, and 6) timing and type of treatment.

            The most common abnormalities on the CBC in animals with cytauxzoonosis include leukopenia with toxic neutrophils and thrombocytopenia with a normocytic, normochromic anemia seen at later stages. The most common biochemical abnormalities are hyperbilirubinemia and hypoalbuminemia but may vary depending on organ systems affected by parasitic thrombosis and ischemia with tissue necrosis. Other, less consistently detected abnormalities include increased liver enzyme concentrations and azotemia.

            Rapid diagnosis requires microscopic observation of piroplasms or schizonts. Observation of piroplasms on blood smears is variable; they are seen in association with increasing body temperature and typically become apparent approximately 1-3 days before death.

            In the absence of these observations, a diagnostic PCR test with greater sensitivity and specificity than microscopy can be done. This test is recommended in suspect cases in which the parasite is not observed, as well as to confirm identification of piroplasms or schizonts.

            Historically, attempts to treat cytauxzoonosis with a variety of antiparasitic drugs (parvaquone, buparvaquone, trimethoprim/sulfadiazine, sodium thiacetarsamide) have been met with little success. In one study, 5 of 6 cats and one additional cat were successfully treated with diminazene aceturate (not approved in the USA) and imidocarb dipropionate (2 mg/kg, IM, 2 injections 3-7 days apart), respectively.

            The most consistent successful treatment in a large case series resulted in survival of 64 percent of cats given a combination of atovaquone (15 mg/kg, PO, tid for 10 days) and azithromycin (10 mg/kg/day, PO, for 10 days) and supportive care. Atovaquone is a ubiquinone analog that binds cytochrome b. In one study of _C. felis_-infected cats treated with atovaquone and azithromycin, a _C. felis_ cytochrome b subtype (cytb1) was identified that was associated with increased survival in the cats infected with this subtype compared with other subtypes. Future development of a rapid means to identify the cytb1 _C. felis_ subtype in infected cats may help better predict the likelihood of survival with treatment.

            Supportive care, including IV fluid therapy and heparin (100-200 U/kg, SC, tid) should be instituted in all cases. Nutritional support via an esophageal or nasoesophageal feeding tube is recommended, which also facilitates administration of oral medications (for example, atovaquone and azithromycin). Oxygen therapy and blood transfusions should be administered when necessary. Anti-inflammatory drugs may be warranted in cases with unrelenting fever; however, the use of NSAIDs is contraindicated in cats with azotemia or dehydration. Once a diagnosis is achieved and treatments have begun, minimal stress and handling are recommended. Recovery, including resolution of fever, is often slow and may take as long as 5-7 days. Cats that survive have a complete clinical recovery, including resolution of hematologic and biochemical abnormalities within 2-3 weeks. Some survivors remain persistently infected with piroplasms and may represent a reservoir of infection. In a recent study, dose-intense diaminazene diaceturate (4 mg/kg/day, IM, for 5 consecutive days) failed to reduce the severity of parasitemia in cats chronically infected with _C. felis_ and resulted in adverse drug reactions.

            Routine application of a tick preventive is recommended to prevent cytauxzoonosis; however, disease has occurred in cats despite this treatment. In a recent study, a tick-repellant collar [Soresto] for cats containing imidacloprid 10 per cent/flumethrin 4.5 per cent prevented _A. americanum_ ticks from attaching, feeding, and transmitting _C. felis_ in 10 cats infested with infected ticks after application of the collar. In the same study, ticks attached and fed on 10 of 10 control cats not treated with a collar, and 9 of the 10 control cats were infected with _C. felis_. Exclusion of cats from areas likely to be infested with the tick vector (that is, indoor only) is still considered the best method of prevention.

            Portions of this comment were extracted from http://www.merckvetmanual.com/mvm/circulatory_system/blood_parasites/cytauxzoonosis.html. - Mod.TG

            A HealthMap/ProMED-mail map can be accessed at: http://healthmap.org/promed/p/238.]"""

        expectedCounts = [
            1,
            1,
            5,
            5,
            56,
            2,
            1,
            2,
            1,
            1,
            2,
            14,
            14,
            10,
            106,
            41,
            3,
            18,
            106,
            41,
            1,
            2,
            3,
            4,
            5,
            6,
            3,
            1,
            5,
            6,
            1,
            2,
            2,
            7,
            15,
            10,
            1,
            200,
            7,
            3,
            4,
            5,
            10,
            10,
            10,
            10,
            9,
            10
        ]
        doc = AnnoDoc(example)
        doc.add_tier(self.annotator)
        self.assertEqual(len(doc.tiers['counts'].spans), len(expectedCounts))
        for actual, expected in zip(doc.tiers['counts'].spans, expectedCounts):
            self.assertEqual(actual.metadata['count'], expected)  

    def test_singular_cases(self):
        examples= [
            ("The index case occured on January 22.", [{'count': 1}]),
            ("A lassa fever case was reported in Hawaii", [{'count':1}])]
        for example in examples:
            sent, counts = example
            doc = AnnoDoc(sent)
            doc.add_tier(self.annotator)
            self.assertEqual(len(doc.tiers['counts'].spans), len(counts))
            for actual, expected in zip(doc.tiers['counts'].spans, counts):
                test_utils.assertHasProps(actual.metadata, expected)
    # def test_year_count(self):
    #     doc = AnnoDoc("""As of [Sun 19 Mar 2017] (epidemiological week 11),
    #     a total of 1407 suspected cases of meningitis have been reported.""")
    #     doc.add_tier(self.annotator)
    #     self.assertEqual(len(doc.tiers['counts']), 1)
    #     test_utils.assertHasProps(
    #         doc.tiers['counts'].spans[0].metadata, {
    #             'count': 1407
    #         })

if __name__ == '__main__':
    unittest.main()
