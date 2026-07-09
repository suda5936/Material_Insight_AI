param(
    [string]$OutputDir = "deliverables"
)

$ErrorActionPreference = "Stop"

function Escape-Xml {
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return "" }
    return $Text.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace('"', "&quot;").Replace("'", "&apos;")
}

function Reset-Dir {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Path | Out-Null
}

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(ValueFromPipeline = $true)]
        [AllowEmptyString()]
        [string]$InputObject
    )
    begin {
        $builder = New-Object System.Text.StringBuilder
    }
    process {
        [void]$builder.AppendLine($InputObject)
    }
    end {
        $encoding = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($Path, $builder.ToString(), $encoding)
    }
}

function Zip-Directory {
    param(
        [string]$SourceDir,
        [string]$DestinationFile
    )
    if (Test-Path -LiteralPath $DestinationFile) {
        Remove-Item -LiteralPath $DestinationFile -Force
    }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $sourceRoot = (Resolve-Path $SourceDir).Path
    $destination = (Resolve-Path (Split-Path $DestinationFile -Parent)).Path + "\" + (Split-Path $DestinationFile -Leaf)
    $zip = [System.IO.Compression.ZipFile]::Open($destination, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | ForEach-Object {
            $relative = $_.FullName.Substring($sourceRoot.Length).TrimStart("\", "/") -replace "\\", "/"
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $relative) | Out-Null
        }
    }
    finally {
        $zip.Dispose()
    }
}

function W-Paragraph {
    param(
        [string]$Text,
        [string]$Style = "",
        [switch]$Bold,
        [switch]$Italic
    )
    $styleXml = ""
    if ($Style) { $styleXml = "<w:pPr><w:pStyle w:val=`"$Style`"/></w:pPr>" }
    $rPr = ""
    if ($Bold -or $Italic) {
        $rPr = "<w:rPr>"
        if ($Bold) { $rPr += "<w:b/>" }
        if ($Italic) { $rPr += "<w:i/>" }
        $rPr += "</w:rPr>"
    }
    return "<w:p>$styleXml<w:r>$rPr<w:t xml:space=`"preserve`">$(Escape-Xml $Text)</w:t></w:r></w:p>"
}

function W-Bullet {
    param([string]$Text)
    return "<w:p><w:pPr><w:pStyle w:val=`"ListParagraph`"/><w:ind w:left=`"720`" w:hanging=`"360`"/></w:pPr><w:r><w:t xml:space=`"preserve`">• $(Escape-Xml $Text)</w:t></w:r></w:p>"
}

function W-PageBreak {
    return "<w:p><w:r><w:br w:type=`"page`"/></w:r></w:p>"
}

function W-CodeBlock {
    param([string[]]$Lines)
    $xml = "<w:p><w:pPr><w:shd w:fill=`"F3F6FA`"/><w:spacing w:before=`"120`" w:after=`"120`"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii=`"Consolas`" w:hAnsi=`"Consolas`"/></w:rPr><w:t xml:space=`"preserve`">"
    $xml += Escape-Xml (($Lines -join "`n"))
    $xml += "</w:t></w:r></w:p>"
    return $xml
}

function W-Table {
    param([array]$Rows)
    $xml = "<w:tbl><w:tblPr><w:tblStyle w:val=`"TableGrid`"/><w:tblW w:w=`"0`" w:type=`"auto`"/></w:tblPr>"
    foreach ($row in $Rows) {
        $xml += "<w:tr>"
        foreach ($cell in $row) {
            $xml += "<w:tc><w:tcPr><w:tcW w:w=`"2400`" w:type=`"dxa`"/></w:tcPr>"
            $xml += W-Paragraph -Text ([string]$cell)
            $xml += "</w:tc>"
        }
        $xml += "</w:tr>"
    }
    $xml += "</w:tbl>"
    return $xml
}

function New-Docx {
    param(
        [string]$Path
    )

    $temp = Join-Path $env:TEMP ("p6_docx_" + [guid]::NewGuid().ToString("N"))
    Reset-Dir $temp
    New-Item -ItemType Directory -Path (Join-Path $temp "_rels") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "word") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "word\_rels") | Out-Null

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
'@ | Write-Utf8File -Path (Join-Path $temp "[Content_Types].xml")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
'@ | Write-Utf8File -Path (Join-Path $temp "_rels\.rels")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
'@ | Write-Utf8File -Path (Join-Path $temp "word\_rels\document.xml.rels")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:sz w:val="21"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:b/><w:sz w:val="36"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:sz w:val="24"/><w:color w:val="555555"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:spacing w:before="360" w:after="160"/></w:pPr><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:b/><w:sz w:val="30"/><w:color w:val="1F4E79"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:b/><w:sz w:val="24"/><w:color w:val="2F5597"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:pPr><w:spacing w:after="80"/></w:pPr><w:rPr><w:rFonts w:ascii="맑은 고딕" w:hAnsi="맑은 고딕" w:eastAsia="맑은 고딕"/><w:sz w:val="21"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/><w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/><w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/></w:tblBorders></w:tblPr></w:style>
</w:styles>
'@ | Write-Utf8File -Path (Join-Path $temp "word\styles.xml")

    $body = ""
    $body += W-Paragraph -Text "건설 공정관리자를 위한 P6 Schedule Recovery Copilot" -Style "Title"
    $body += W-Paragraph -Text "관심 산업 기반 AI Agent 도입 전략 및 Delivery 설계 최종 보고서" -Style "Subtitle"
    $body += W-Paragraph -Text "주제: 건설 산업의 공정관리자를 위해, Critical Path 지연 영향 분석과 복구 대안 검토 시간을 줄이는 AI Agent 설계" -Style "Subtitle"
    $body += W-Paragraph -Text "작성일: 2026년 7월 9일" -Style "Subtitle"
    $body += W-PageBreak

    $body += W-Paragraph -Text "목차" -Style "Heading1"
    @(
        "1. 주제 선정 배경",
        "2. 산업 및 업무 특성 분석",
        "3. 현재 AI 도입 현황",
        "4. 향후 AI Agent 도입 후보 10개",
        "5. MVP Agent 선정 이유",
        "6. Agent 사용자 시나리오",
        "7. 입력·출력과 필요한 데이터",
        "8. 기술 아키텍처와 업무 흐름",
        "9. RAG 및 Human-in-the-loop 설계",
        "10. 위험 요소와 통제 방안",
        "11. 평가 지표",
        "12. 프로토타입 및 데모 시나리오",
        "13. 기대 효과와 한계",
        "14. Delivery 전략",
        "15. 참고문헌"
    ) | ForEach-Object { $body += W-Bullet $_ }
    $body += W-PageBreak

    $body += W-Paragraph -Text "1. 주제 선정 배경" -Style "Heading1"
    $body += W-Paragraph -Text "본 과제의 주제는 건설 산업의 공정관리자를 위한 P6 Schedule Recovery Copilot이다. 건설 프로젝트는 다수 이해관계자와 수많은 선후행 작업이 얽힌 프로젝트형 산업이며, 한 Activity의 지연이 후속 공정과 준공일에 연쇄적으로 영향을 미칠 수 있다. 특히 Critical Path에 포함된 작업이 지연되면 단순히 날짜를 조정하는 것이 아니라 Activity logic, calendar, float, 실제 진도, 품질·안전 절차, 승인 조건, 복구 가능성을 함께 다시 검토해야 한다."
    $body += W-Paragraph -Text "따라서 본 보고서는 AI가 P6를 자동으로 수정하는 시스템이 아니라, 공정관리자의 분석과 의사결정을 보조하는 Copilot을 설계한다. 핵심은 자연어 현장 이슈를 구조화하고, 관련 Activity와 근거 문서를 찾고, 결정론적 일정 엔진으로 CPM 영향을 계산한 뒤, 사람이 검토할 수 있는 복구 대안과 보고서를 생성하는 것이다."
    $body += W-Paragraph -Text "주제 문장: 나는 건설 산업의 공정관리자를 위해, Critical Path 지연 영향 분석과 복구 대안 검토에 드는 시간을 줄이는 AI Agent를 설계한다." -Bold
    $body += W-Paragraph -Text "객관적 근거로 본 프로젝트 필요성" -Style "Heading2"
    $body += W-Table @(
        @("근거", "해석", "본 프로젝트와의 연결"),
        @("건설 생산성 문제", "McKinsey 관련 보도와 산업 분석은 건설 생산성 증가가 장기간 낮았고, 정보 단절과 현장 조정 비용이 큰 문제임을 지적한다.", "단순 자동화보다 일정·문서·승인 판단을 연결하는 업무 보조가 필요하다."),
        @("P6의 산업적 위치", "Oracle Primavera P6는 대형 프로젝트의 일정, 자원, 비용 통제에 쓰이는 프로젝트 포트폴리오 관리 도구다.", "공정관리자의 실제 기준 데이터가 P6 Activity와 Relationship이므로 Agent도 이 구조를 중심으로 설계해야 한다."),
        @("건설 AI 도입 흐름", "Procore, OpenSpace, Autodesk는 문서 검색, 현장 기록, 시공 데이터 활용을 AI로 지원하고 있다.", "AI 도입 방향은 타당하지만, CP 지연 복구 분석은 문서 검색만으로 해결되지 않아 CPM 계산 엔진과 결합해야 한다."),
        @("생성형 AI 연구", "건설 분야 생성형 AI 연구는 RAG가 답변 품질과 재현성을 개선할 수 있음을 보여준다.", "현장 문서 근거를 citation으로 제한하고, 일정 계산은 결정론적으로 분리하는 설계가 필요하다.")
    )
    $body += W-Paragraph -Text "핵심 객관 지표" -Style "Heading2"
    $body += W-Table @(
        @("지표", "수치", "의미"),
        @("건설 노동생산성 증가율", "연평균 약 1%", "전 세계 경제 전체 평균 2.8%, 제조업 3.6%와 비교해 낮다. 공정관리와 현장 조정의 디지털 개선 여지가 크다."),
        @("생산성 격차의 경제적 기회", "약 1.6조 달러", "건설 생산성이 전체 경제 수준을 따라잡을 경우 창출 가능한 가치로 제시된다."),
        @("Megaproject 연간 지출 규모", "약 6~9조 달러", "대형 프로젝트 관리는 세계 GDP의 약 8% 수준으로 평가될 만큼 경제적 비중이 크다."),
        @("Megaproject 성과 문제", "10개 중 9개 cost overrun", "대형 건설·인프라 프로젝트에서 비용·기간 초과가 반복된다는 연구가 있다."),
        @("본 MVP의 직접 개선 대상", "Activity 탐색, 근거 검색, CPM 재계산, 보고서 초안", "경제 전체 생산성을 직접 바꾸는 것이 아니라 공정관리자의 반복 분석 시간을 줄이는 좁은 문제를 겨냥한다.")
    )

    $body += W-Paragraph -Text "2. 산업 및 업무 특성 분석" -Style "Heading1"
    $body += W-Paragraph -Text "건설 산업은 발주자, 설계사, 시공사, 감리·CM, 협력업체, 공급업체가 계약과 공정표를 중심으로 협업하는 산업이다. 공정관리자는 일정 작성, 진도 업데이트, 지연 분석, 복구계획 작성, 보고와 승인 추적을 담당한다."
    $body += W-Table @(
        @("이해관계자", "주요 역할"),
        @("발주자", "사업 목표, 예산, 준공일, 주요 승인"),
        @("시공사", "공사 수행, 공정·품질·안전·원가 관리"),
        @("공정관리자", "일정 작성, 진도 업데이트, 지연 분석, 복구계획"),
        @("협력업체", "전문 공종 수행, 자원 투입, 현장 피드백"),
        @("감리/CM", "공정 검토, 품질 확인, 승인")
    )
    $body += W-Paragraph -Text "공정관리 업무 흐름은 기준 일정 수립, 주기적 진도 업데이트, 현장 이슈 수집, 관련 Activity 확인, 일정 영향 분석, 복구 대안 수립, 현장 검토, 관리자 승인, 수정 일정 또는 Recovery Schedule 작성, 보고 및 추적으로 이어진다."
    $body += W-Paragraph -Text "이 업무가 어려운 이유는 지연이 하나의 작업에만 머물지 않기 때문이다. P6 일정망에서 Activity는 선후행 관계로 연결되어 있고, 어떤 작업은 Total Float을 갖지만 어떤 작업은 Critical Path에 포함되어 준공일에 직접 영향을 준다. 또한 현장 문서에는 지연 원인, 승인 여부, 품질·안전 조건, 협력업체 책임, 대체 작업 가능성 같은 비정형 정보가 흩어져 있다. 따라서 공정관리자는 구조화 데이터와 문서 근거를 동시에 읽고 판단해야 한다."
    $body += W-Paragraph -Text "본 프로젝트가 다루는 핵심 병목은 바로 이 연결 작업이다. AI가 일정관리자를 대체하는 것이 아니라, 현장 문제를 Activity 후보와 문서 근거로 연결하고, 계산 가능한 부분은 코드가 재현 가능하게 처리하며, 판단이 필요한 부분은 명시적으로 사람에게 돌려주는 방식이 현실적이다."
    @(
        "반복 업무: 작업일보와 회의록 확인, Activity ID 검색, 선후행 관계 확인, 보고서 표와 설명 작성",
        "판단 업무: 실제 연결 Activity 판단, Critical 또는 near-critical 영향 판단, 기간 단축 가능성 판단, 승인 필요성 판단",
        "주요 데이터: Project, WBS, Activity, Relationship, Duration, Total Float, Baseline, Actual Date, 문서 근거",
        "주요 위험: 잘못된 Activity 매핑, 문서 품질 문제, 계약·안전·품질 판단의 책임 문제, P6 고유 calendar와 constraint 재현 한계"
    ) | ForEach-Object { $body += W-Bullet $_ }

    $body += W-Paragraph -Text "3. 현재 AI 도입 현황" -Style "Heading1"
    $body += W-Paragraph -Text "건설 산업의 AI는 문서 검색, 현장 기록, 진행률 추적, 설계·시공 데이터 연결, 리스크 탐지 방향으로 발전하고 있다. 본 과제는 최소 3개 사례 요건을 충족하기 위해 4개 사례를 검토했다."
    $body += W-Table @(
        @("사례", "해결 문제", "AI 기술", "사용자", "한계"),
        @("Procore AI", "분산된 문서와 현장 데이터를 찾아 업무 action으로 연결", "RAG, agentic workflow, 문서 질의", "PM, 현장 관리자, 시공사", "플랫폼 내 데이터 품질과 권한 설정에 의존"),
        @("OpenSpace", "현장 상태 기록과 진행률 확인의 수작업 부담", "360 이미지, visual intelligence, BIM/도면 매핑", "현장 관리자, 품질 담당자, 발주자", "촬영 품질과 주기, 최종 판단은 사람 검토 필요"),
        @("Autodesk AI", "설계·시공 데이터 활용과 설계/Make workflow 지원", "생성형 AI, 설계 데이터 분석", "설계자, 엔지니어, 시공 관리자", "기업 데이터 표준화와 시스템 연결 필요"),
        @("Oracle Primavera P6", "대형 프로젝트의 일정·자원·비용 통제", "CPM schedule, resource/cost management", "Scheduler, PMO, 공정관리자", "AI Agent가 아니므로 지연 원인 구조화와 보고서 초안화는 별도 필요")
    )
    $body += W-Paragraph -Text "시사점은 명확하다. 건설 AI는 이미 문서 탐색과 현장 가시화에는 적용되고 있으나, Critical Path 지연 발생 시 Activity mapping, 근거 검색, deterministic CPM 계산, 복구 scenario 작성, review 보고서를 하나의 흐름으로 연결하는 현장형 Copilot에는 기회가 남아 있다."
    $body += W-Paragraph -Text "특히 현재 사례들은 각자 강점이 분명하지만 한계도 있다. Procore 계열 AI는 프로젝트 정보 검색과 업무 자동화에 강하지만, 사용자의 특정 P6 schedule network를 deterministic하게 재계산하는 도구는 아니다. OpenSpace 계열은 시각적 현장 진척 확인에 강하지만, 이미지 기반 진행률이 곧바로 계약상 일정 영향이나 recovery schedule로 변환되지는 않는다. Autodesk AI는 설계·시공 데이터 활용 범위가 넓지만, 특정 현장 지연 이슈의 Activity 후보 선정과 CPM 영향 계산은 별도 업무 설계가 필요하다. Oracle Primavera P6는 일정 통제의 기준 도구지만 자연어 이슈 구조화, RAG 근거 검색, 보고서 초안 생성은 AI Agent 영역으로 남는다."

    $body += W-PageBreak
    $body += W-Paragraph -Text "4. 향후 AI Agent 도입 후보 10개" -Style "Heading1"
    $body += W-Table @(
        @("후보", "대상 사용자", "문제", "효과", "난이도/위험"),
        @("CP 지연 복구 Copilot", "공정관리자", "CP 지연 분석과 복구안 작성 지연", "분석·보고 시간 단축", "중/중"),
        @("회의록 Action Item Agent", "PM/현장소장", "회의 결과 추적 누락", "조치사항 자동 구조화", "하/중"),
        @("RFI 영향 분석 Agent", "설계·시공 담당자", "RFI 일정 영향 판단 지연", "관련 Activity와 문서 연결", "중/중"),
        @("Submittal 지연 추적 Agent", "품질/공무", "승인 지연에 따른 공정 영향 파악", "승인 병목 조기 탐지", "중/중"),
        @("자재 납기 리스크 Agent", "구매/공정", "자재 지연 조기 발견 어려움", "납기 위험 사전 경고", "중/중"),
        @("NCR 재시공 영향 Agent", "QA/QC", "품질 문제의 일정 영향 분석", "재작업 Activity 초안", "중/상"),
        @("Daily Report 요약 Agent", "현장 관리자", "작업일보 검토 부담", "진도·이슈 요약", "하/중"),
        @("안전 조치 일정 영향 Agent", "안전관리자", "작업중지/조치의 일정 영향", "승인 전 체크리스트", "중/상"),
        @("Change Order 초안 Agent", "계약/공무", "변경 영향 설명 작성 부담", "근거 기반 초안", "상/상"),
        @("Near-critical Watch Agent", "Scheduler", "Float 소진 작업 관리", "조기 경보", "중/중")
    )
    $body += W-Paragraph -Text "MVP로는 CP 지연 복구 Copilot을 선정한다. 이유는 사용자가 명확하고, 데이터가 Activity/Relationship CSV와 현장 문서로 제한 가능하며, 일정 계산은 결정론적 코드로 검증 가능하고, AI는 해석·생성·검토 역할로 제한할 수 있기 때문이다."

    $body += W-Paragraph -Text "5. MVP Agent 선정 이유" -Style "Heading1"
    @(
        "업무 중요도: Critical Path 지연은 준공일, 계약, 비용, 현장 자원에 직접 영향을 준다.",
        "반복성과 판단의 공존: Activity 검색과 보고서 작성은 반복적이지만, 복구 가능성·승인·책임은 사람 판단이 필요하다.",
        "데이터 접근성: P6 export CSV, 회의록, 작업일보, RFI, 승인 문서 등 MVP 입력을 명확히 제한할 수 있다.",
        "기술 적합성: LLM, RAG, deterministic CPM engine, rule validator, human-in-the-loop를 조합하기 좋다.",
        "위험 통제 가능성: AI가 계산하거나 승인하지 않도록 역할을 분리하면 환각과 책임 문제를 줄일 수 있다.",
        "Delivery 타당성: Schedule Engine과 RAG를 단계적으로 구현하면 실제 완성도와 설계 일치도를 검증하면서 확장할 수 있다."
    ) | ForEach-Object { $body += W-Bullet $_ }
    $body += W-Paragraph -Text "즉 이 프로젝트는 '건설에 AI를 붙인다'는 넓은 주제가 아니라, 공정관리자가 실제로 반복 수행하는 CP 지연 영향 분석 패키지를 빠르게 구성하게 돕는 좁고 검증 가능한 Agent 설계다. 이 점이 과제에서 요구한 구체적 사용자, 구체적 업무, 현실적 Delivery 관점에 부합한다."

    $body += W-Paragraph -Text "6. Agent 사용자 시나리오" -Style "Heading1"
    $body += W-Paragraph -Text "Actor는 시공사 공정관리자다. 사전조건은 Activity CSV, Relationship CSV, 현장 문서가 프로젝트에 업로드되어 있고, 분석 대상 schedule snapshot이 선택되어 있는 상태다."
    $body += W-CodeBlock @(
        "Trigger: A동 12층 커튼월 자재 납품이 10일 지연됨",
        "1. 사용자가 자연어 issue를 입력한다.",
        "2. 시스템이 관련 Activity 후보와 근거 문서를 검색한다.",
        "3. Mapper가 issue type, location, trade, delay days, impact mode를 구조화한다.",
        "4. confidence가 부족하면 사용자가 Activity를 직접 선택한다.",
        "5. Schedule Engine이 baseline CPM과 impact CPM을 계산한다.",
        "6. Planner가 허용 action으로 복구 scenario 3개를 만든다.",
        "7. Simulator가 scenario별 recovered days를 계산한다.",
        "8. Validator와 Reviewer가 오류, 근거 부족, 승인 필요사항을 표시한다.",
        "9. 시스템이 Markdown 보고서 초안을 생성한다."
    )
    $body += W-Paragraph -Text "예외 흐름도 설계한다. Activity 매칭이 불확실하면 NEEDS_ACTIVITY_SELECTION 상태로 전환한다. 관련 문서가 없으면 no relevant evidence로 표시하되 일정 계산은 수행한다. 일정 네트워크에 cycle이 있으면 CPM 계산을 중단하고 schedule data correction을 요구한다. Agent가 존재하지 않는 Activity ID 또는 evidence chunk ID를 반환하면 validator가 reject한다."

    $body += W-PageBreak
    $body += W-Paragraph -Text "7. 입력·출력과 필요한 데이터" -Style "Heading1"
    $body += W-Table @(
        @("구분", "내용"),
        @("입력 1", "Activity CSV: activity_id, name, wbs, duration, status, baseline/actual/remaining 정보"),
        @("입력 2", "Relationship CSV: predecessor_id, successor_id, type, lag"),
        @("입력 3", "현장 문서 TXT/MD: 회의록, 작업일보, RFI, NCR, 자재 납기 메일, 시공계획서"),
        @("입력 4", "사용자 issue: 자연어 지연 상황 설명"),
        @("출력 1", "Activity 후보와 confidence"),
        @("출력 2", "RAG evidence chunk와 citation"),
        @("출력 3", "Baseline/Impact CPM 결과"),
        @("출력 4", "복구 scenario 3개와 recovered days"),
        @("출력 5", "Validator/Reviewer 결과와 Markdown 보고서")
    )
    $body += W-Paragraph -Text "필요한 도구는 FastAPI, PostgreSQL, pg_trgm, pgvector, SQLAlchemy Async, Alembic, NetworkX, OpenAI API, vLLM Qwen/Gemma이다. OpenAI는 API key 기반 호출만 사용하고, vLLM은 현재 사용 가능한 Qwen과 Gemma endpoint를 전제로 한다."

    $body += W-Paragraph -Text "8. 기술 아키텍처와 업무 흐름" -Style "Heading1"
    $body += W-CodeBlock @(
        "[사용자]",
        "  -> CSV/문서/Issue 입력",
        "[FastAPI API]",
        "  -> Analysis Orchestrator",
        "     -> Activity Candidate Search(pg_trgm)",
        "     -> RAG Retrieval(pgvector)",
        "     -> Issue Mapping Agent(vLLM Qwen)",
        "     -> Schedule Engine(Python/NetworkX)",
        "     -> Recovery Planning Agent(OpenAI API)",
        "     -> Rule Validator(Python)",
        "     -> Review Agent(vLLM Gemma, OpenAI fallback)",
        "     -> Report Builder",
        "[PostgreSQL]",
        "  -> schedules, issues, agent_runs, retrieval_runs, reports"
    )
    $body += W-Paragraph -Text "역할 분리가 핵심이다. LLM은 해석·생성·검토를 담당한다. 일반 코드는 CPM 계산, validation, evidence allowlist, confidence rule, report assembly를 담당한다. RAG는 현장 문서 근거를 제공하지만 일정 수치를 계산하지 않는다."

    $body += W-Paragraph -Text "9. RAG 및 Human-in-the-loop 설계" -Style "Heading1"
    $body += W-Paragraph -Text "RAG는 TXT/MD 문서를 1200자 chunk와 200자 overlap으로 분할하고, project filter와 metadata filter를 적용한 뒤 vector top 20을 가져오고 threshold와 metadata boost를 적용해 최종 top 8을 반환한다. 점수는 vector similarity 0.70, trade match 0.10, location match 0.10, approval status 0.05, recency 0.05로 구성한다."
    $body += W-Paragraph -Text "Human-in-the-loop는 Activity 선택, 복구 scenario 선택, P6 반영, 안전 승인, 품질 승인, 비용 승인, 계약/EOT 판단에 적용한다. Activity 자동 선택은 top1 confidence 0.85 이상, top1-top2 gap 0.10 이상, activity가 미완료 상태, snapshot 내 ID 존재 조건을 모두 만족할 때만 허용한다."

    $body += W-Paragraph -Text "10. 위험 요소와 통제 방안" -Style "Heading1"
    $body += W-Table @(
        @("위험", "통제 방안"),
        @("잘못된 Activity 매핑", "confidence threshold와 human selection"),
        @("LLM의 일정 수치 환각", "ES/EF/LS/LF/TF/project delay는 Python만 계산"),
        @("존재하지 않는 근거 인용", "retrieved evidence allowlist 검증"),
        @("과거 사례의 오용", "metadata와 reviewer warning 표시"),
        @("계약·안전 판단 오용", "자동 승인 금지, human confirmation 필수"),
        @("P6와 MVP 계산 차이", "FS-only, 7-day calendar 등 MVP 제한 명시")
    )

    $body += W-PageBreak
    $body += W-Paragraph -Text "11. 평가 지표" -Style "Heading1"
    $body += W-Table @(
        @("영역", "지표"),
        @("업무 효과", "Activity 탐색 시간, 보고서 작성 시간, scenario 작성 시간, human confirmation까지 소요 시간"),
        @("Agent 품질", "Activity mapping precision, missing information detection, JSON schema validity, hallucination rate"),
        @("RAG 품질", "relevant chunk recall, citation correctness, no-evidence handling, metadata filter accuracy"),
        @("Schedule Engine", "CPM calculation correctness, cycle detection, delay impact accuracy, recovered-day calculation correctness"),
        @("사용성", "사용자 수정 횟수, 결과 이해도, 승인 전 검토 누락률")
    )

    $body += W-Paragraph -Text "12. 프로토타입 및 데모 시나리오" -Style "Heading1"
    $body += W-Paragraph -Text "데모는 구현 범위를 과장하지 않고, 설계 기반 프로토타입 흐름으로 제시한다. 사용자는 샘플 Activity CSV, Relationship CSV, 회의록/자재 지연 문서, 자연어 issue를 입력한다."
    $body += W-CodeBlock @(
        "샘플 issue:",
        "A동 12층 커튼월 자재 납품이 10일 지연되어 설치 시작이 지연될 가능성이 있습니다.",
        "",
        "기대 출력:",
        "- Activity 후보: CW-A-12-010 등",
        "- Evidence: 회의록/납기 메일 chunk",
        "- Impact mode: START_BLOCK",
        "- Baseline/Impact CPM: Python 계산 결과",
        "- Scenario 1: 시작 block 5일 감소",
        "- Scenario 2: 후속 설치 duration 3일 단축",
        "- Scenario 3: 시작 block 감소 + duration 단축 조합",
        "- Reviewer warning: 야간작업/품질/안전 승인 필요",
        "- Markdown report 생성"
    )

    $body += W-Paragraph -Text "13. 기대 효과와 한계" -Style "Heading1"
    @(
        "기대 효과: 공정관리자의 Activity 탐색과 문서 근거 확인 시간을 줄인다.",
        "기대 효과: 복구 대안 초안을 표준화해 보고서 작성 시간을 줄인다.",
        "기대 효과: Agent/RAG/계산 trace를 남겨 결과 검토 가능성을 높인다.",
        "한계: MVP는 FS relationship과 단순 calendar만 지원한다.",
        "한계: resource leveling, cost estimating, live P6 writeback은 제외한다.",
        "한계: 현장 실행 가능성과 계약 책임은 반드시 사람이 판단해야 한다."
    ) | ForEach-Object { $body += W-Bullet $_ }

    $body += W-Paragraph -Text "14. Delivery 전략" -Style "Heading1"
    $body += W-Paragraph -Text "Delivery는 데이터와 계산 검증을 먼저 수행하고, 이후 RAG, Agent, 사용자 검증, 확장 순서로 진행한다. 이 순서는 설계와 구현의 일치도를 높이기 위한 것이다."
    $body += W-Table @(
        @("단계", "목표"),
        @("1단계", "Project/Snapshot/Activity/Relationship import와 validation"),
        @("2단계", "CPM Schedule Engine 단위 테스트"),
        @("3단계", "Project-scoped RAG와 evidence allowlist"),
        @("4단계", "Mapper/Planner/Reviewer agent 연결"),
        @("5단계", "Orchestrator, report, frontend demo"),
        @("6단계", "사용자 피드백 기반 확장")
    )

    $body += W-Paragraph -Text "15. 참고문헌 및 출처" -Style "Heading1"
    @(
        "Procore. Procore AI: https://www.procore.com/en-sg/ai",
        "OpenSpace. Visual Intelligence Platform for Builders: https://www.openspace.ai/",
        "Autodesk. Autodesk AI: https://www.autodesk.com/solutions/autodesk-ai",
        "Oracle. Primavera P6 Enterprise Project Portfolio Management: https://www.oracle.com/construction-engineering/primavera-p6/",
        "McKinsey Global Institute 관련 산업 분석 보도. 건설 노동생산성 연 1%, 세계 경제 2.8%, 제조업 3.6%, 생산성 개선 잠재 가치 1.6조 달러: https://www.axios.com/2021/08/28/startups-closing-construction-productivity-gap",
        "Bent Flyvbjerg. What You Should Know About Megaprojects, and Why: 연간 megaproject 지출 6~9조 달러, 세계 GDP 약 8%, iron law of megaprojects: https://arxiv.org/abs/1409.0003",
        "The New Yorker. The Trouble with Megaprojects: 10개 중 9개 megaproject cost overrun 언급: https://www.newyorker.com/news/news-desk/bertha-seattle-infrastructure-trouble-megaprojects",
        "Taiwo et al. Generative AI in the Construction Industry: A State-of-the-art Analysis, arXiv:2402.09939",
        "Ersoz. Demystifying the Potential of ChatGPT-4 Vision for Construction Progress Monitoring, arXiv:2412.16108",
        "프로젝트 내부 문서: docs/p6-schedule-recovery-copilot-integrated-ko.md",
        "프로젝트 내부 문서: docs/p6-schedule-recovery-copilot-phase-summary-ko.md"
    ) | ForEach-Object { $body += W-Bullet $_ }

    $body += "<w:sectPr><w:pgSz w:w=`"11906`" w:h=`"16838`"/><w:pgMar w:top=`"1440`" w:right=`"1440`" w:bottom=`"1440`" w:left=`"1440`" w:header=`"708`" w:footer=`"708`" w:gutter=`"0`"/></w:sectPr>"

    $document = "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><w:document xmlns:w=`"http://schemas.openxmlformats.org/wordprocessingml/2006/main`"><w:body>$body</w:body></w:document>"
    $document | Write-Utf8File -Path (Join-Path $temp "word\document.xml")

    Zip-Directory -SourceDir $temp -DestinationFile $Path
    Remove-Item -LiteralPath $temp -Recurse -Force
}

function A-TextParagraph {
    param(
        [string]$Text,
        [int]$Size = 2000,
        [switch]$Bold,
        [switch]$Bullet
    )
    $bu = ""
    if ($Bullet) { $bu = "<a:buChar char=`"•`"/>" }
    $b = if ($Bold) { " b=`"1`"" } else { "" }
    return "<a:p>$bu<a:r><a:rPr lang=`"ko-KR`" sz=`"$Size`"$b/><a:t>$(Escape-Xml $Text)</a:t></a:r></a:p>"
}

function P-TextBox {
    param(
        [int]$Id,
        [string]$Name,
        [string[]]$Lines,
        [int]$X,
        [int]$Y,
        [int]$Cx,
        [int]$Cy,
        [int]$FontSize = 2000,
        [switch]$Title,
        [switch]$Fill
    )
    $fillXml = if ($Fill) { "<a:solidFill><a:srgbClr val=`"EAF2F8`"/></a:solidFill>" } else { "<a:noFill/>" }
    $lineXml = if ($Fill) { "<a:ln><a:solidFill><a:srgbClr val=`"4F81BD`"/></a:solidFill></a:ln>" } else { "<a:ln><a:noFill/></a:ln>" }
    $paras = ""
    $i = 0
    foreach ($line in $Lines) {
        if ($Title -and $i -eq 0) {
            $paras += A-TextParagraph -Text $line -Size $FontSize -Bold
        } else {
            $paras += A-TextParagraph -Text $line -Size $FontSize -Bullet:(!$Title)
        }
        $i++
    }
    return @"
<p:sp>
  <p:nvSpPr><p:cNvPr id="$Id" name="$(Escape-Xml $Name)"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr><a:xfrm><a:off x="$X" y="$Y"/><a:ext cx="$Cx" cy="$Cy"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>$fillXml$lineXml</p:spPr>
  <p:txBody><a:bodyPr wrap="square" anchor="t"/><a:lstStyle/>$paras</p:txBody>
</p:sp>
"@
}

function New-SlideXml {
    param(
        [string]$Title,
        [string[]]$Bullets,
        [string[]]$Boxes = @()
    )
    $spTree = @"
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
"@
    $spTree += P-TextBox -Id 2 -Name "Title" -Lines @($Title) -X 480000 -Y 250000 -Cx 11200000 -Cy 650000 -FontSize 3400 -Title
    if ($Bullets.Count -gt 0) {
        $spTree += P-TextBox -Id 3 -Name "Bullets" -Lines $Bullets -X 780000 -Y 1100000 -Cx 10400000 -Cy 4300000 -FontSize 2050
    }
    $id = 10
    foreach ($box in $Boxes) {
        $parts = $box -split "\|", 5
        $spTree += P-TextBox -Id $id -Name "Box$id" -Lines @($parts[4]) -X ([int]$parts[0]) -Y ([int]$parts[1]) -Cx ([int]$parts[2]) -Cy ([int]$parts[3]) -FontSize 1750 -Title -Fill
        $id++
    }
    return @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>$spTree</p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"@
}

function New-Pptx {
    param([string]$Path)

    $slides = @(
        @{ title="P6 Schedule Recovery Copilot"; bullets=@("건설 공정관리자를 위한 AI Agent 도입 전략", "Critical Path 지연 영향 분석과 복구 대안 검토 지원", "P6 자동 수정이 아닌 Human-in-the-loop 의사결정 지원") },
        @{ title="문제 정의"; bullets=@("CP 작업이 밀리면 일정망 전체를 다시 검토해야 함", "Activity logic, float, 실제 진도, 승인 조건, 복구 대안을 함께 판단", "수작업 분석과 보고서 작성에 많은 시간이 소요") },
        @{ title="왜 건설 공정관리인가"; bullets=@("건설은 다수 조직이 계약·일정·문서로 협업하는 프로젝트형 산업", "생산성 정체와 현장 정보 단절이 반복적으로 지적되는 분야", "P6는 대형 프로젝트 일정 통제의 기준 도구이지만 자연어 이슈 해석과 보고서 초안화는 별도 업무", "따라서 AI Agent는 P6를 대체하는 것이 아니라 분석 패키지를 빠르게 준비하는 보조 역할이 적합") },
        @{ title="객관 지표로 본 필요성"; bullets=@("건설 노동생산성 증가율: 연평균 약 1%", "전 세계 경제 전체: 2.8%, 제조업: 3.6%", "생산성 격차 개선 잠재 가치: 약 1.6조 달러", "Megaproject 지출: 연간 약 6~9조 달러, 세계 GDP 약 8%", "대형 프로젝트는 10개 중 9개가 비용 초과를 겪는다는 연구 존재") },
        @{ title="산업·업무 특성"; bullets=@("건설은 다수 이해관계자가 일정·계약·문서 중심으로 협업하는 산업", "공정관리자는 일정 작성, 진도 업데이트, 지연 분석, 복구계획을 담당", "문서 기반 근거와 현장 판단이 함께 필요") },
        @{ title="현재 AI 도입 현황"; bullets=@("Procore: 문서·프로젝트 데이터 기반 AI agent와 cited answer 제공", "OpenSpace: 360 이미지와 visual intelligence로 현장 기록·진행률 확인", "Autodesk: 설계·Make workflow에 AI 적용", "Oracle Primavera P6: 대형 프로젝트 일정·자원·비용 통제의 기준 도구") },
        @{ title="Agent 후보 10개"; bullets=@("CP 지연 복구 Copilot, 회의록 Action Item Agent, RFI 영향 분석 Agent", "Submittal 지연 추적, 자재 납기 리스크, NCR 재시공 영향", "Daily Report 요약, 안전 조치 일정 영향, Change Order 초안, Near-critical Watch") },
        @{ title="MVP 선정 이유"; bullets=@("Critical Path 지연은 준공일·비용·계약에 직접 영향", "CSV 일정 데이터와 TXT/MD 현장 문서로 MVP 입력 제한 가능", "LLM은 해석·생성·검토, Python은 일정 계산으로 역할 분리 가능", "Human-in-the-loop로 책임과 환각 위험 통제") },
        @{ title="MVP 핵심 흐름"; bullets=@("Project/Snapshot 생성 -> Activity/Relationship CSV import", "현장 문서 upload -> chunking/embedding -> RAG 검색", "Issue 입력 -> Activity mapping -> CPM impact 계산", "복구 scenario 3개 -> validation/review -> Markdown report") },
        @{ title="아키텍처"; bullets=@(); boxes=@("700000|1300000|2200000|700000|사용자 입력", "3300000|1300000|2400000|700000|FastAPI API", "6200000|1300000|2700000|700000|Analysis Orchestrator", "9500000|1300000|1900000|700000|Report", "1700000|2600000|2300000|700000|PostgreSQL pg_trgm/pgvector", "4700000|2600000|2300000|700000|Python CPM Engine", "7700000|2600000|2500000|700000|Qwen/OpenAI/Gemma Agents") },
        @{ title="Agent 역할 분리"; bullets=@("Mapper(vLLM Qwen): issue 구조화와 Activity 후보 재순위화", "Planner(OpenAI): 허용 action으로 정확히 3개 scenario 생성", "Rule Validator(Python): ID/evidence/action/confidence 검증", "Reviewer(vLLM Gemma): 근거 누락과 human decision point 검토") },
        @{ title="RAG와 일정 계산의 경계"; bullets=@("RAG는 현장 문서 근거 제공과 citation 추적에 사용", "일정 계산은 ES/EF/LS/LF/TF/project delay/recovered days를 Python으로 계산", "LLM은 schedule number를 만들거나 수정할 수 없음", "근거가 없으면 no relevant evidence로 표시하고 계산은 별도 수행") },
        @{ title="Human-in-the-loop"; bullets=@("Activity 자동 선택은 confidence 0.85 이상, top1-top2 gap 0.10 이상일 때만 허용", "조건 미달 시 NEEDS_ACTIVITY_SELECTION", "P6 반영, safety, quality, cost, contract/EOT 판단은 사람 승인 필요") },
        @{ title="위험 통제와 평가 지표"; bullets=@("위험: 잘못된 매핑, 환각, 허위 citation, P6 계산 차이, 계약/안전 오용", "통제: allowlist, rule validator, deterministic engine, reviewer warning, approval gate", "평가: mapping precision, citation correctness, CPM correctness, 보고서 작성 시간 감소") },
        @{ title="데모 시나리오와 기대 효과"; bullets=@("예시: A동 12층 커튼월 자재 납품 10일 지연", "출력: Activity 후보, RAG 근거, impact CPM, 복구 scenario 3개, review warning, report", "효과: 분석 구조화, 근거 추적, 보고서 초안화, 담당자 판단 시간 단축") }
    )

    $temp = Join-Path $env:TEMP ("p6_pptx_" + [guid]::NewGuid().ToString("N"))
    Reset-Dir $temp
    New-Item -ItemType Directory -Path (Join-Path $temp "_rels") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "ppt\_rels") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "ppt\slides") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "ppt\slides\_rels") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "ppt\slideMasters\_rels") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "ppt\slideLayouts\_rels") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $temp "ppt\theme") | Out-Null

    $overrides = ""
    for ($i = 1; $i -le $slides.Count; $i++) {
        $overrides += "  <Override PartName=`"/ppt/slides/slide$i.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.presentationml.slide+xml`"/>`n"
    }
    @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
$overrides</Types>
"@ | Write-Utf8File -Path (Join-Path $temp "[Content_Types].xml")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>
'@ | Write-Utf8File -Path (Join-Path $temp "_rels\.rels")

    $rels = "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`">"
    $sldIds = "<p:sldIdLst>"
    for ($i = 1; $i -le $slides.Count; $i++) {
        $rels += "<Relationship Id=`"rId$i`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide`" Target=`"slides/slide$i.xml`"/>"
        $slideId = 255 + $i
        $sldIds += "<p:sldId id=`"$slideId`" r:id=`"rId$i`"/>"
        $slide = $slides[$i - 1]
        New-SlideXml -Title $slide.title -Bullets $slide.bullets -Boxes $slide.boxes | Write-Utf8File -Path (Join-Path $temp "ppt\slides\slide$i.xml")
        "<?xml version=`"1.0`" encoding=`"UTF-8`" standalone=`"yes`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`"><Relationship Id=`"rId1`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout`" Target=`"../slideLayouts/slideLayout1.xml`"/></Relationships>" | Write-Utf8File -Path (Join-Path $temp "ppt\slides\_rels\slide$i.xml.rels")
    }
    $masterRelId = $slides.Count + 1
    $rels += "<Relationship Id=`"rId$masterRelId`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster`" Target=`"slideMasters/slideMaster1.xml`"/>"
    $rels += "</Relationships>"
    $sldIds += "</p:sldIdLst>"
    $rels | Write-Utf8File -Path (Join-Path $temp "ppt\_rels\presentation.xml.rels")

    @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId$masterRelId"/></p:sldMasterIdLst>
  $sldIds
  <p:sldSz cx="12192000" cy="6858000" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>
"@ | Write-Utf8File -Path (Join-Path $temp "ppt\presentation.xml")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>
'@ | Write-Utf8File -Path (Join-Path $temp "ppt\slideMasters\slideMaster1.xml")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
'@ | Write-Utf8File -Path (Join-Path $temp "ppt\slideMasters\_rels\slideMaster1.xml.rels")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
'@ | Write-Utf8File -Path (Join-Path $temp "ppt\slideLayouts\slideLayout1.xml")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
'@ | Write-Utf8File -Path (Join-Path $temp "ppt\slideLayouts\_rels\slideLayout1.xml.rels")

    @'
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="P6 Copilot">
  <a:themeElements>
    <a:clrScheme name="P6"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F4E79"/></a:dk2><a:lt2><a:srgbClr val="EAF2F8"/></a:lt2><a:accent1><a:srgbClr val="1F4E79"/></a:accent1><a:accent2><a:srgbClr val="70AD47"/></a:accent2><a:accent3><a:srgbClr val="FFC000"/></a:accent3><a:accent4><a:srgbClr val="C00000"/></a:accent4><a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="A5A5A5"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="P6"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface="맑은 고딕"/></a:majorFont><a:minorFont><a:latin typeface="Arial"/><a:ea typeface="맑은 고딕"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="P6"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>
'@ | Write-Utf8File -Path (Join-Path $temp "ppt\theme\theme1.xml")

    Zip-Directory -SourceDir $temp -DestinationFile $Path
    Remove-Item -LiteralPath $temp -Recurse -Force
}

$root = (Resolve-Path ".").Path
$out = Join-Path $root $OutputDir
if (-not (Test-Path -LiteralPath $out)) {
    New-Item -ItemType Directory -Path $out | Out-Null
}

New-Docx -Path (Join-Path $out "P6_Schedule_Recovery_Copilot_Final_Report.docx")
New-Pptx -Path (Join-Path $out "P6_Schedule_Recovery_Copilot_Presentation.pptx")

Write-Host "Generated:"
Write-Host (Join-Path $out "P6_Schedule_Recovery_Copilot_Final_Report.docx")
Write-Host (Join-Path $out "P6_Schedule_Recovery_Copilot_Presentation.pptx")









