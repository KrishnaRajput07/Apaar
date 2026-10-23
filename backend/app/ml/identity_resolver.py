import math
from typing import Dict, Any, List, Optional, Tuple

def jaro_similarity(s1: str, s2: str) -> float:
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = (max(len1, len2) // 2) - 1
    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    transpositions = 0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    transpositions = transpositions // 2
    return (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3.0

def jaro_winkler(s1: str, s2: str, p: float = 0.1, max_l: int = 4) -> float:
    j = jaro_similarity(s1, s2)
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    prefix = 0
    for i in range(min(len(s1), len(s2), max_l)):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break
    return j + (prefix * p * (1.0 - j))

def levenshtein_distance(s1: str, s2: str) -> int:
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[m][n]

def soundex(name: str) -> str:
    name = "".join(filter(str.isalpha, name.upper()))
    if not name:
        return "0000"
    first = name[0]
    mapping = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6'
    }
    encoded = [first]
    for char in name[1:]:
        code = mapping.get(char, '0')
        if code != '0' and code != encoded[-1]:
            encoded.append(code)
    out = "".join(encoded).replace('0', '')
    return (out + "0000")[:4]

class IdentityResolutionEngine:
    """
    Cross-institution entity resolution & fuzzy deduplication engine.
    """
    def compute_similarity(
        self,
        record1: Dict[str, Any],
        record2: Dict[str, Any]
    ) -> Dict[str, Any]:
        name1 = record1.get("name", "")
        name2 = record2.get("name", "")
        
        jw_name = jaro_winkler(name1, name2)
        phonetic_match = soundex(name1) == soundex(name2)
        lev_dist = levenshtein_distance(name1, name2)

        # DOB match
        dob1 = record1.get("dob", "")
        dob2 = record2.get("dob", "")
        dob_match = 1.0 if (dob1 and dob2 and dob1 == dob2) else 0.0

        # Guardian similarity
        g1 = record1.get("guardian", "")
        g2 = record2.get("guardian", "")
        jw_guardian = jaro_winkler(g1, g2) if (g1 and g2) else 0.5

        # Weighted composite score
        # Name: 50%, DOB: 30%, Guardian/Phone: 20%
        composite = (jw_name * 0.50) + (dob_match * 0.30) + (jw_guardian * 0.20)
        
        # Phonetic boost if soundex matches despite spelling variation (e.g. Kiran Reddy vs Kiran Redy)
        if phonetic_match and composite < 0.95:
            composite = min(1.0, composite + 0.08)

        match_score_pct = int(round(composite * 100))

        if match_score_pct >= 90:
            classification = "HIGH_CONFIDENCE_MATCH"
            recommendation = "Auto-Merge candidate or Immediate Officer Review"
        elif match_score_pct >= 72:
            classification = "CANDIDATE_DUPLICATE"
            recommendation = "Flagged for Officer Cross-Verification"
        else:
            classification = "DISTINCT_INDIVIDUAL"
            recommendation = "No identity conflict detected"

        return {
            "compositeScore": match_score_pct,
            "classification": classification,
            "recommendation": recommendation,
            "metrics": {
                "nameJaroWinkler": round(jw_name, 3),
                "nameLevenshteinDistance": lev_dist,
                "phoneticMatch": phonetic_match,
                "dobExactMatch": dob_match == 1.0,
                "guardianJaroWinkler": round(jw_guardian, 3)
            }
        }
