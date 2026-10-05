// nlprobe: does NaturalLanguage's language recognizer tell the Latin-script languages Vision does not list from English?
// (the text of short UI-like labels in each language; prints dominant language and confidence)
import NaturalLanguage

let samples: [(String, String)] = [
    ("ca", "Configuració\nInicia la sessió\nHistorial d'entrenaments\nCompartir amb amics\nSurt de l'aplicació"),
    ("hr", "Postavke\nPočni vježbu\nPovijest treninga\nPodijeli s prijateljima\nOdjava iz aplikacije"),
    ("hu", "Beállítások\nEdzés indítása\nElőzmények\nMegosztás barátokkal\nKijelentkezés az alkalmazásból"),
    ("sk", "Nastavenia\nZačať tréning\nHistória tréningov\nZdieľať s priateľmi\nOdhlásiť sa z aplikácie"),
    ("sl", "Nastavitve\nZačni vadbo\nZgodovina vadb\nDeli s prijatelji\nOdjava iz aplikacije"),
    ("en", "Settings\nStart workout\nWorkout history\nShare with friends\nSign out of the app"),
]
for (want, text) in samples {
    let r = NLLanguageRecognizer(); r.processString(text)
    let h = r.languageHypotheses(withMaximum: 3).sorted { $0.value > $1.value }.map { "\($0.key.rawValue)=\(String(format: "%.2f", $0.value))" }
    print(want, "->", h.joined(separator: " "))
}
