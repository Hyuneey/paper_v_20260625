# Dashboard V2 접근성

- 문서 언어 `ko`, semantic header/nav/main/section/aside/table을 사용한다.
- skip link와 모든 keyboard action에 visible focus를 제공한다.
- SVG node는 `role=button`, `tabindex=0`, 설명형 `aria-label`을 가진다.
- 상태는 색뿐 아니라 text와 `aria-label`로 표시한다.
- chart는 exact-value table을 제공한다.
- drawer tab은 `role=tab`, `aria-selected`; drawer는 `aria-hidden`을 갱신한다.
- 900px 이하에서 navigation을 접고 680px 이하에서 drawer를 full-screen으로 전환한다.
- `prefers-reduced-motion`에서 transition/animation을 사실상 제거한다.
- print에서 navigation과 interaction control을 숨기고 table overflow를 해제한다.

키보드, 1440×900/1366×768/1920×1080/390×844 화면, 한글 줄바꿈은 final visual QA에서 확인한다.
