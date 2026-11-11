// BU DOSYA OTOMATİK ÜRETİLİR. Düzenleme: Tools/fontgen/build_fonts.py

extension CharacterCatalog {
    static let all: [PatiCharacter] = [
        PatiCharacter(
            id: "cat",
            name: "Kedi",
            clips: [AnimationClip(id: "tail", title: "Kuyruk sallama", fontName: "Pati-cat-tail"), AnimationClip(id: "breathe", title: "Uykuda nefes", fontName: "Pati-cat-breathe"), AnimationClip(id: "walk", title: "Yürüyüş", fontName: "Pati-cat-walk"), AnimationClip(id: "roll", title: "Yuvarlanma", fontName: "Pati-cat-roll")],
            poseFontName: "Pati-cat-poses",
            poses: ["a", "s", "z", "t", "p"]
        ),
    ]
}
