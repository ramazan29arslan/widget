// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py

extension CharacterCatalog {
    static let all: [PatiCharacter] = [
        PatiCharacter(
            id: "cat",
            name: "Kedi",
            clips: [
                AnimationClip(id: "tail", title: "Kuyruk sallama", fontName: "Pati-cat-tail", leftFont: nil, rightFont: nil),
                AnimationClip(id: "breathe", title: "Uykuda nefes", fontName: "Pati-cat-breathe", leftFont: nil, rightFont: nil),
                AnimationClip(id: "roll", title: "Yuvarlanma", fontName: "Pati-cat-roll", leftFont: nil, rightFont: nil),
                AnimationClip(id: "walk", title: "Yürüyüş", fontName: "Pati-cat-walk", leftFont: "Pati-cat-walk-L", rightFont: "Pati-cat-walk-R"),
                AnimationClip(id: "mouse", title: "Fare kovalama", fontName: "Pati-cat-mouse", leftFont: "Pati-cat-mouse-L", rightFont: "Pati-cat-mouse-R"),
                AnimationClip(id: "yarn", title: "Yumak kovalama", fontName: "Pati-cat-yarn", leftFont: "Pati-cat-yarn-L", rightFont: "Pati-cat-yarn-R"),
            ],
            poseFontName: "Pati-cat-poses",
            poses: ["a", "s", "z", "t", "p"],
            moodClips: ["awake": "tail", "sleepy": "breathe", "sleeping": "breathe", "tired": "breathe", "playful": "yarn"]
        ),
        PatiCharacter(
            id: "dog",
            name: "Köpek",
            clips: [
                AnimationClip(id: "tail", title: "Kuyruk sallama", fontName: "Pati-dog-tail", leftFont: nil, rightFont: nil),
                AnimationClip(id: "breathe", title: "Uykuda nefes", fontName: "Pati-dog-breathe", leftFont: nil, rightFont: nil),
                AnimationClip(id: "roll", title: "Yuvarlanma", fontName: "Pati-dog-roll", leftFont: nil, rightFont: nil),
                AnimationClip(id: "walk", title: "Yürüyüş", fontName: "Pati-dog-walk", leftFont: "Pati-dog-walk-L", rightFont: "Pati-dog-walk-R"),
                AnimationClip(id: "fetch", title: "Top getirme", fontName: "Pati-dog-fetch", leftFont: "Pati-dog-fetch-L", rightFont: "Pati-dog-fetch-R"),
            ],
            poseFontName: "Pati-dog-poses",
            poses: ["a", "s", "z", "t", "p"],
            moodClips: ["awake": "tail", "sleepy": "breathe", "sleeping": "breathe", "tired": "breathe", "playful": "fetch"]
        ),
        PatiCharacter(
            id: "janissary",
            name: "Atlı Yeniçeri",
            clips: [
                AnimationClip(id: "guard", title: "Nöbet", fontName: "Pati-janissary-guard", leftFont: nil, rightFont: nil),
                AnimationClip(id: "battle", title: "Savaş", fontName: "Pati-janissary-battle", leftFont: nil, rightFont: nil),
                AnimationClip(id: "march", title: "Sefere gidiş", fontName: "Pati-janissary-march", leftFont: "Pati-janissary-march-L", rightFont: "Pati-janissary-march-R"),
                AnimationClip(id: "charge", title: "Hücum", fontName: "Pati-janissary-charge", leftFont: "Pati-janissary-charge-L", rightFont: "Pati-janissary-charge-R"),
            ],
            poseFontName: "Pati-janissary-poses",
            poses: ["a", "s", "z", "t", "p"],
            moodClips: ["awake": "guard", "sleepy": "guard", "sleeping": "guard", "tired": "guard", "playful": "charge"]
        ),
    ]
}
