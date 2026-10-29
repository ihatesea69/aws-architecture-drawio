---
name: auto/aws-architecture-drawio
description: Vẽ sơ đồ kiến trúc AWS bằng draw.io theo phong cách riêng của người dùng (icon AWS4 đặt gần nhau, mũi tên đánh số, chú giải + tiêu đề lớn, không ô ghi chú) từ script Python, và kiểm bằng đo (hình học, XML, tên icon, lint style, xuất PNG)
triggers: draw.io diagram, drawio, mxGraph XML, AWS architecture diagram, architecture diagram style, vẽ kiến trúc, sơ đồ kiến trúc, vẽ drawio, Sidebar-AWS4, resIcon, verify diagram without screenshot, export diagram png for README
source: auto
created_at: 2026-10-28T08:15:03+00:00
updated_at: 2026-10-29T16:20:00+00:00
---

## Khi nào dùng
Dùng cho mọi sơ đồ kiến trúc AWS cần ra file `.drawio`, thường kèm một ảnh PNG cho README hoặc slide, ở bất kỳ
project nào. Skill này chỉ quy định cách vẽ, không quy định vẽ cái gì.

Mọi luật trong mục "Phong cách" đều đo từ hai sơ đồ người dùng đã tự hoàn thiện bằng tay trong draw.io: một file
3 trang và một file 1 trang, tổng cộng 4 trang, 62 mũi tên, 60 icon. Chỗ nào bản sửa tay khác bản script sinh ra
thì theo bản sửa tay, và skill ghi rõ chỗ đó.

Ngày 2026-10-29 người dùng yêu cầu đổi cỡ trên một sơ đồ 1080 x 1080: "cho các icon bự lên, mũi tên cũng bự lên,
fill đầy 1080 x 1080 nhưng không bị trùng lấp". Từ đó cỡ chuẩn là icon 80 px, nhãn 13 px, mũi tên 2,5 px,
số 30 px. Cỡ cũ (60 / 11 / 1,5 / 24) chỉ còn đúng với hai sơ đồ đã sửa tay trước ngày đó.

## Phong cách

### Khung trang
- Trang vuông 1080 x 1080. Hệ thống lớn thì dùng trang to hơn, nhưng vẫn vuông.
- Cell đầu tiên là một hình chữ nhật nền trắng, cách mép trang 10 px, viền đen mảnh
  (`fillColor=#FFFFFF;strokeColor=#000000;`). Nhờ hình nền này mà ảnh PNG xuất ra vuông và có nền trắng.
- Font mặc định của draw.io (Helvetica). Màu chữ `#232F3E`.
- Chữ trên sơ đồ viết tiếng Anh nếu sơ đồ được công khai; còn lại viết cùng ngôn ngữ với tài liệu đi kèm.

### Khung nhóm
| Khung | Style |
|---|---|
| AWS account | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;` viền liền `#CD2264`, tiêu đề `#CD2264` 13 px đậm, `spacingLeft=30`, không tô nền |
| Region | `grIcon=mxgraph.aws4.group_region;` viền đứt `#00A4A6`, tiêu đề `#147EBA` 13 px đậm, nằm trong account, cách mép trái 20 px và mép trên 30 px |
| Khung logic (một stack, một giải pháp, một đơn vị deploy) | hình chữ nhật trơn, viền liền `#CD2264`, tiêu đề `#CD2264` 13 px đậm ở góc trên trái, `spacingLeft=8;spacingTop=2;`, không icon, không tô nền |
| Step Functions workflow | dùng group chính thức `group_aws_step_functions_workflow`, màu `#CD2264` |
| VPC (`d.vpc()`) | group chính thức `group_vpc2`, viền liền tím `#8C4FFF`, tiêu đề tím. VPC luôn vẽ bằng khung này, không bao giờ bằng khung logic hồng |
| Availability Zone (`d.az()`) | hình chữ nhật viền đứt xanh `#147EBA`, tiêu đề căn giữa phía trên, đúng style trong sidebar |
| Subnet (`d.subnet(public=True/False)`) | `group_security_group` không viền icon: public viền `#7AA116` nền `#F2F6E8`, private viền `#00A4A6` nền `#E6F6F7` |
| Compute trên Fargate (`d.service()`) | hình chữ nhật viền đứt cam `#ED7100` dày 2 px, không tiêu đề. Bên trong đặt icon AWS Fargate và mỗi vai trò **một** Task (`d.glyph(..., "ecs_task", ...)`) |

- Resource có hình riêng trong AWS4 thì vẽ ra, không chỉ ghi vào tên khung. Ví dụ NAT Gateway: `d.glyph(..., "nat_gateway", ...)`
  đặt trong public subnet của AZ chứa nó. Người dùng đã hỏi "sao lại không vẽ NAT gateway" khi nó chỉ nằm trong tên khung.
- Gọn: mỗi vai trò một task, một khung Fargate chung cho cả cluster. Tách mỗi service một khung, hoặc vẽ
  nhiều task cho cùng một vai trò, đã bị người dùng chê là quá nhiều ("sao nhiều Service Task vậy? gọn lại").
- Khung compute có thể nằm ngang qua cả hai cột AZ, giống hình mẫu ECS của AWS mà người dùng gửi.

- Các account đặt cạnh nhau, cách nhau 30 px: account nguồn hoặc của khách bên trái, account trung tâm hoặc quản lý bên phải.
- Tiêu đề khung ghi vai trò ("Customer account", "Central account"), không bao giờ ghi account ID hay tên khách.
- Khung logic đặt tên theo việc nó làm ("Usage analytics"), không theo tên repo sinh ra nó. Tên repo ghi vào một dòng chú giải.

### Icon và nhãn
- Mọi icon có kích thước 80 x 80, lấy từ thư viện AWS4: `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<tên>;`,
  `strokeColor=#ffffff`. Màu nền của icon là màu mà palette của chính draw.io gán cho icon đó (`colors_from_sidebar()`).
- Hình dạng nét của AWS4 (Task, NAT Gateway, ...) vẽ bằng `d.glyph()`, cùng ô 80 x 80, màu theo họ dịch vụ
  (cam cho container, tím cho networking).
- Người dùng vẽ bằng `shape=mxgraph.aws4.user`, màu `#232F3D` ("Developer", "Viewers").
- Sản phẩm không có icon AWS4 thì dùng logo của chính sản phẩm, ảnh 80 x 80 (`Diagram.logo()`, nhúng dạng data URI).
  Không mượn một icon AWS không liên quan.
- Nhãn icon: 13 px **đậm**, màu `#232F3E`, tối đa 2 dòng. Dòng 1 là tên dịch vụ ("Amazon S3", "Lambda"), dòng 2 là
  vai trò của nó trong kiến trúc ("raw data", "collector"). Mỗi dòng nên dưới 20 ký tự; trung vị đo được là 10-11 ký tự.
  Trên trang 1080 nhiều icon thì chỉ dùng 1 dòng tên, vai trò để chú giải nói.
  Người dùng đã tự tay in đậm 33 trong 35 nhãn, nên nhãn chữ thường do script sinh ra chính là thứ đã bị sửa.
- Nhãn mặc định nằm dưới icon. Khi có mũi tên đi ra từ cạnh dưới icon thì đặt nhãn lên trên, hoặc sang trái/phải.
  Mũi tên không bao giờ cắt qua chữ.
- Bố trí gần nhau nhưng lấp đầy trang: khoảng 110-140 px giữa tâm hai icon cùng hàng, 130-220 px giữa hai icon
  cùng cột. Khung và icon trải hết trang 1080 x 1080, chú giải và tiêu đề lấp phần dưới.
- Người dùng có thể cố ý giữ một icon cũ, ví dụ `quicksight` cho dashboard. Thư viện hiện tại đã bỏ icon này
  nhưng draw.io vẫn vẽ được. Phải tôn trọng lựa chọn đó: truyền icon vào `--allow-missing`, rồi chứng minh icon
  vẫn hiện bằng `png_measure.py`.

### Mũi tên và số
- Mũi tên: `edgeStyle=none;rounded=0;endArrow=block;endFill=1;strokeColor=#545B64;strokeWidth=2.5;endSize=8;`.
  Chỉ có đoạn ngang và đoạn dọc, đường đi đặt bằng waypoint cụ thể, và hai đầu đều gắn vào hình.
- Mũi tên nét đứt (`dashed=1;strokeColor=#879596;`) chỉ dùng cho một nghĩa, thường là "account trung tâm chủ động
  đọc account kia" (pull, AssumeRole). Chú giải phải ghi nét đứt nghĩa là gì.
- Không ghi chữ trên mũi tên nào (0 trên 62 mũi tên có chữ). Mũi tên nào quan trọng thì đánh số.
- Số: hình tròn 30 x 30, nền `#232F3E`, viền trắng 2 px, số trắng 14 px đậm. Tâm của số đặt cách đường kẻ 22 px,
  không bao giờ đè lên đường: phía trên đoạn ngang, bên phải đoạn dọc, trên đoạn dài nhất của mũi tên.
  Khi đoạn đó cắt qua viền khung, dời số bằng `badge_t` (vị trí 0..1 trên đoạn), `badge_seg` (chọn đoạn khác)
  hoặc `badge="left"/"below"`, cho tới khi `check()` hết báo "sits on the border".
- Số chạy từ 1 đến N theo thứ tự đọc: trái sang phải, trên xuống dưới, theo dòng dữ liệu.
- Nhiều mũi tên cùng đi vào một icon thì vào ở các điểm khác nhau trên một cạnh (`entry=(0, 0.25)`, `(0, 0.75)`),
  không nhập thành một đường. Mũi tên giữa hai account đi qua khoảng trống giữa hai khung account.

### Chú giải và tiêu đề
- Chú giải: một ô chữ ở góc dưới bên trái, ngay dưới các khung. Chữ 10 px **đậm**, màu `#545B64`, không viền,
  không tô nền, mỗi dòng cao 13 px. Mỗi số một dòng, dạng `N  một câu đơn giản.` (số, khoảng trắng không ngắt
  cộng một khoảng trắng, rồi câu). Giờ chạy, lịch, điều kiện và "chưa xác minh" đều ghi ở đây, không ghi trên sơ đồ.
- Sau các dòng có số là vài dòng không số: nét đứt nghĩa là gì, tên khung logic ứng với cái gì, và các giả định
  về phạm vi ("các account này có thể là account riêng").
- Tiêu đề: 44 px **đậm**, màu `#232F3E`, hai dòng, căn giữa trong khoảng trống bên phải chú giải (góc dưới bên phải).
  Người dùng đã tự kéo tiêu đề 16 px ở góc trên trái xuống đây và phóng to lên.

### Không bao giờ đặt lên sơ đồ
- Ô ghi chú, ô callout, khối tô màu, bảng, đoạn văn. Cái gì cần một câu để giải thích thì ghi vào chú giải.
  Điểm chưa xác minh cũng không đánh dấu bằng ô ghi chú đỏ; ghi "not yet verified" trong dòng chú giải.
- Tên khách hàng, account ID, Identity Store ID, ARN có số account, tên người thật (`lint_style.py --public`).
- Dấu gạch ngang dài (em dash).

## Quy trình
1. Tải thư viện icon một lần mỗi phiên vào `$KIROCREW_SCRATCH`. Thư viện này thay đổi theo thời gian nên không chép sẵn vào skill:
   `https://raw.githubusercontent.com/jgraph/drawio/dev/src/main/webapp/js/diagramly/sidebar/Sidebar-AWS4.js`
2. Chép `examples/build_example.py` (hai account) hoặc `examples/build_vpc_fargate_example.py` (VPC, AZ, subnet,
   NAT Gateway, khung Fargate) vào project rồi thay bố cục. Giữ nguyên thứ tự gọi: khung, icon, mũi tên,
   `legend()`, `title()`, `check()`, `write()`. Toạ độ là pixel tuyệt đối trên trang; thư viện tự đổi sang toạ độ
   tương đối theo khung cha mà draw.io lưu. Mọi hằng số style nằm trong `scripts/aws_drawio.py`: import thư viện,
   đừng gõ lại style.
3. Chỉnh bố cục tới khi `d.check()` trả về `[]`. Hàm này bắt: nhãn chồng nhau, phần tử tràn khung, mũi tên cắt
   qua icon, nhãn hoặc số, đoạn chéo, hai đường nhập làm một, số nằm trên viền khung hoặc đè lên đường, số không
   chạy đủ 1..N, chú giải lệch với số. `d.crossings()` đếm số chỗ hai mũi tên cắt nhau: được phép, nhưng giữ ít.
4. Kiểm file độc lập với script đã sinh ra nó:
   `python scripts/verify_drawio.py <file.drawio> <Sidebar-AWS4.js> [--allow-missing=quicksight]`
   (XML đọc được, 0 mũi tên lơ lửng, mọi tên `mxgraph.aws4` đều có trong thư viện, mọi hình nằm trong trang).
5. Lint style: `python scripts/lint_style.py <file.drawio> [--public]`. FAIL là vi phạm luật phong cách: có ô ghi chú,
   có chữ trên mũi tên, nhãn 3 dòng, số trùng hoặc thiếu, chú giải lệch số, mũi tên không gắn vào hình, hoặc có
   định danh khi chạy với `--public`. WARN là điểm lệch cần xem lại. Lint chạy được cả trên file sửa tay.
6. Xuất PNG bằng draw.io desktop CLI. Phải tìm đường dẫn `draw.io.exe`, vì nó không phải lúc nào cũng có trong PATH:
   `& "<đường dẫn>\draw.io.exe" -x -f png -s 2 -o <out.png> <file.drawio>`
   rồi chạy `python scripts/png_measure.py <out.png> <file.drawio> 2`. Kết quả đúng là: ảnh vuông; chỉ có các chunk
   IHDR/IDAT/IEND, tức không nhúng XML của sơ đồ trong PNG; và mỗi ô icon có khoảng 8-21 % điểm trắng (đo trên hai ví dụ
   ở cỡ 80 px; script không đo được hình dạng nét như Task và NAT Gateway). Icon trống,
   tức tên icon không tồn tại, đo ra gần 0 %. Script tự từ chối đo khi PNG không khớp với file.
7. Báo cáo từng phép kiểm đã đo được gì, và nói rõ là màu sắc và độ cân đối chưa được đánh giá: người dùng tự mở
   file để xem. Trên máy này, không tự kiểm file local bằng cách chụp màn hình headless.

## Khi người dùng đã sửa file bằng tay
- Từ lúc đó, file sửa tay là nguồn chính. Cho script sinh sơ đồ từ chối ghi vào đường dẫn đó, và chỉ sửa đúng phần
  được yêu cầu (ví dụ dịch nhãn). So từng dòng với bản sao lưu, giữ nguyên số cell và toạ độ, rồi lint và xuất lại.
- Sửa tay thường để lại những thứ cần báo cho người dùng chứ không tự ý sửa: đầu mũi tên chưa gắn vào hình, một icon
  trùng bị che dưới icon khác, số bị kéo đè lên đường. `lint_style.py` tìm ra những chỗ này.

## Bẫy cần tránh
- Escape mọi nhãn bằng `xml.sax.saxutils.escape`; thư viện đã làm sẵn. Một chuỗi thô như `<customer>` trong nhãn
  bị draw.io hiểu là thẻ HTML và chữ sẽ biến mất.
- Waypoint (`mxPoint`) của mũi tên tính theo khung cha của chính mũi tên đó; mũi tên có cha là một group thì lưu
  toạ độ tương đối theo group. Thư viện luôn đặt mũi tên ở cấp trang.
- Data URI ảnh trong draw.io không có phần `;base64` (`image=data:image/png,<base64>`), vì dấu `;` dùng để tách các
  khoá style.
- Amazon Quick có icon riêng là `quick_suite`. Sản phẩm nào có icon riêng thì dùng icon đó.
- Không chạy Python inline trong PowerShell (`python -c` có dấu nháy); viết ra file `.py` rồi chạy file đó.
- Không chạy song song một lệnh tạo file và một lệnh sửa chính file đó: lệnh sửa có thể chạy trước khi file tồn tại.
- Ghi file `.drawio` bằng UTF-8, xuống dòng LF; khi sửa file của người dùng thì giữ nguyên kiểu xuống dòng của họ.
