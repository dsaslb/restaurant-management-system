# GitHub Actions 설정 및 CODECOV_TOKEN 문제 해결

## 문제 원인
GitHub Actions에서 `CODECOV_TOKEN`을 사용하려면 GitHub Secrets에 해당 토큰이 설정되어 있어야 합니다. 이 토큰이 설정되지 않았거나 잘못된 경우, 워크플로우에서 환경 변수를 통해 접근할 수 없습니다.

## 해결 방안
1. **GitHub Secrets 설정**
   - GitHub 저장소로 이동합니다.
   - 저장소의 "Settings" 탭을 클릭합니다.
   - 왼쪽 사이드바에서 "Secrets and variables" > "Actions"를 선택합니다.
   - "New repository secret" 버튼을 클릭합니다.
   - 다음과 같이 입력합니다:
     - Name: `CODECOV_TOKEN`
     - Value: Codecov에서 발급받은 토큰 값

2. **Codecov 토큰 얻기**
   - [Codecov.io](https://codecov.io)에 로그인합니다.
   - 프로젝트 설정으로 이동합니다.
   - "Settings" > "General"에서 토큰을 확인하거나 새로 생성할 수 있습니다.

## GitHub Actions 워크플로우에서의 사용
GitHub Actions 워크플로우 파일에서 다음과 같이 토큰을 사용할 수 있습니다:

```yaml
env:
  CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

## 주의사항
- 보안을 위해 토큰은 절대 코드에 직접 입력하지 마시고, 반드시 GitHub Secrets를 통해 관리해야 합니다. 