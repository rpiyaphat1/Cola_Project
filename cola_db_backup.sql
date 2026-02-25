--
-- PostgreSQL database dump
--

\restrict Gmf6WLoKLUmHHSzKFotdPca294bM51H7DHq6cYUTQCvoVATnO7cE9sQ8tkbjnYT

-- Dumped from database version 14.21 (Homebrew)
-- Dumped by pg_dump version 14.21 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: students; Type: TABLE; Schema: public; Owner: piyaphatrattanarak
--

CREATE TABLE public.students (
    id integer NOT NULL,
    nickname character varying(50),
    fullname character varying(150) NOT NULL,
    grade character varying(20) NOT NULL,
    disability_type character varying(50),
    technique text
);


ALTER TABLE public.students OWNER TO piyaphatrattanarak;

--
-- Name: students_id_seq; Type: SEQUENCE; Schema: public; Owner: piyaphatrattanarak
--

CREATE SEQUENCE public.students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.students_id_seq OWNER TO piyaphatrattanarak;

--
-- Name: students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piyaphatrattanarak
--

ALTER SEQUENCE public.students_id_seq OWNED BY public.students.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: piyaphatrattanarak
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    password character varying(200) NOT NULL
);


ALTER TABLE public."user" OWNER TO piyaphatrattanarak;

--
-- Name: user_access; Type: TABLE; Schema: public; Owner: piyaphatrattanarak
--

CREATE TABLE public.user_access (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    accessible_grade character varying(20),
    accessible_student_id integer
);


ALTER TABLE public.user_access OWNER TO piyaphatrattanarak;

--
-- Name: user_access_id_seq; Type: SEQUENCE; Schema: public; Owner: piyaphatrattanarak
--

CREATE SEQUENCE public.user_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_access_id_seq OWNER TO piyaphatrattanarak;

--
-- Name: user_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piyaphatrattanarak
--

ALTER SEQUENCE public.user_access_id_seq OWNED BY public.user_access.id;


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: piyaphatrattanarak
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO piyaphatrattanarak;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: piyaphatrattanarak
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: piyaphatrattanarak
--

CREATE TABLE public.users (
    username character varying(80) NOT NULL,
    password character varying(300) NOT NULL,
    displayname character varying(100) NOT NULL,
    permission character varying(20)
);


ALTER TABLE public.users OWNER TO piyaphatrattanarak;

--
-- Name: students id; Type: DEFAULT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.students ALTER COLUMN id SET DEFAULT nextval('public.students_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: user_access id; Type: DEFAULT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.user_access ALTER COLUMN id SET DEFAULT nextval('public.user_access_id_seq'::regclass);


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: piyaphatrattanarak
--

COPY public.students (id, nickname, fullname, grade, disability_type, technique) FROM stdin;
2	ทด	ทดสอบ ครับ	ป.1/1	5	เกด
3	เจเจ	ธีรเดช มีทรัพย์	ป.1/1	ภาษาไทย, คณิตศาสตร์	ปัญหา: อ่านสะกดคำไม่คล่อง และสับสนเครื่องหมายบวก/ลบ | วิธีรับมือ: ฝึกอ่านแจกลูกคำวันละ 10 นาที และใช้สื่อของเล่นตัวเลขช่วยสอน
4	เจเจ	ธาวิน ใจดี	ป.1/1	คณิตศาสตร์	ปัญหา: สับสนการนับเพิ่ม/ลด | วิธีรับมือ: ใช้ฝาขวดน้ำช่วยนับจำนวนจริง
5	เจเจ	กฤษฎา มาดี	ป.2/1	ภาษาอังกฤษ, ภาษาไทย, ศิลปะ	ปัญหา: จำศัพท์ไม่ได้ เขียนหัวพยัญชนะบอด และระบายสีออกนอกเส้น | วิธีรับมือ: เน้นการฟังเพลงภาษาอังกฤษ ฝึกคัดลายมือตามรอยประ และฝึกกล้ามเนื้อมือ
6	ต้นกล้า	พงศกร รักษ์ดี	ป.1/2	วิทยาศาสตร์	ปัญหา: จับใจความการทดลองไม่ได้ | วิธีรับมือ: ให้ดูวิดีโอการทดลองแทนการอ่าน
7	บีม	พงศกร ใจซื่อ	ป.1/2	ภาษาไทย, สังคมศึกษาฯ	ปัญหา: เขียนสลับตำแหน่ง และจำวันสำคัญทางศาสนาไม่ได้ | วิธีรับมือ: ใช้บัตรคำสีช่วยจำตำแหน่ง และเล่านิทานเกี่ยวกับวันสำคัญ
8	นิว	พงศกร แซ่ตั้ง	ป.2/1	คณิตศาสตร์, วิทยาศาสตร์	ปัญหา: คำนวณเงินทอนผิด จำแนกสัตว์ไม่ได้ | วิธีรับมือ: เล่นบทบาทสมมติซื้อขายของ และพาไปดูของจริงในสวน
9	กาย	พงศกร คงกระพัน	ป.3/2	ภาษาอังกฤษ	ปัญหา: เขียนตามคำบอกไม่ได้เลย | วิธีรับมือ: อนุญาตให้สอบปากเปล่าแทนการเขียน
10	ออย	มานะ เรียนเก่ง	ป.1/1	ภาษาไทย, การงานอาชีพฯ	ปัญหา: อ่านข้ามคำ และผูกเงื่อนเชือกไม่ได้ | วิธีรับมือ: ใช้นิ้วชี้ตามตัวอักษรขณะอ่าน และฝึกผูกเชือกรองเท้ากับหุ่นจำลอง
11	แป้ง	วีระ เรียนเก่ง	ป.2/1	คณิตศาสตร์	ปัญหา: ตีโจทย์ปัญหาไม่ได้ | วิธีรับมือ: วาดรูปประกอบโจทย์ปัญหาให้เห็นภาพ
12	ฝน	สุดา เรียนเก่ง	ป.3/1	วิทยาศาสตร์, คณิตศาสตร์	ปัญหา: จำวงจรชีวิตสัตว์สลับกัน และหารยาวไม่ได้ | วิธีรับมือ: ใช้แผนภาพวงจรชีวิตแบบหมุนได้ และฝึกสูตรคูณแม่ 2-5 ให้แม่นยำ
13	มิว	นรากร สอนดี	ป.1/1	ภาษาไทย	ปัญหา: เขียนตัวหนังสือหัวกลับ (Mirror Writing) | วิธีรับมือ: ฝึกเขียนบนกระบะทรายหรือแป้งปั้น
14	พี	อภิชาต พลอย	ป.1/2	ภาษาอังกฤษ, ศิลปะ	ปัญหา: ออกเสียงตัวอักษรเพี้ยน และวาดรูปทรงเรขาคณิตเบี้ยว | วิธีรับมือ: ฝึกออกเสียงหน้ากระจก และใช้แม่พิมพ์วาดรูปช่วย
15	ฟ้า	รัตนา มณีวงศ์	ป.2/2	คณิตศาสตร์, สุขศึกษาฯ	ปัญหา: ท่องสูตรคูณไม่ได้ และแยกซ้ายขวาไม่ถูก | วิธีรับมือ: เปิดเพลงสูตรคูณช่วยจำ และผูกเชือกสีที่ข้อมือขวา
16	อาร์ม	ธนพล วงศ์สา	ป.3/1	ภาษาไทย	ปัญหา: ผันวรรณยุกต์ไม่ได้ (ปา ป่า ป้า) | วิธีรับมือ: ใช้นิ้วมือ 5 นิ้วแทนเสียงวรรณยุกต์
17	เต้ย	จิรายุ เจริญสุข	ป.4/2	วิทยาศาสตร์, การงานอาชีพฯ	ปัญหา: บันทึกผลการทดลองไม่เป็นลำดับ และใช้อุปกรณ์ช่างไม่ถูกวิธี | วิธีรับมือ: ใช้แบบฟอร์มบันทึกที่มีรูปภาพ และสาธิตวิธีใช้อุปกรณ์ช้าๆ
18	พลอย	ณัฐวุฒิ มั่นคง	ป.5/1	ภาษาอังกฤษ, ภาษาไทย	ปัญหา: เรียงประโยคผิดทั้งไทยและอังกฤษ | วิธีรับมือ: ใช้บัตรคำเรียงประโยค (Word Card)
19	แนน	ภาณุพงศ์ เพิ่มพูน	ป.6/2	คณิตศาสตร์	ปัญหา: ดูนาฬิกาแบบเข็มไม่เป็น | วิธีรับมือ: ใช้นาฬิกาจำลองหมุนเข็มเองได้
20	บาส	วรวุฒิ รุ่งเรือง	ป.1/1	ภาษาไทย, สังคมศึกษาฯ, ศิลปะ	ปัญหา: แยก ก/ถ/ภ ไม่ออก ไม่เข้าใจแผนที่ และแยกสีไม่ออก | วิธีรับมือ: ใช้สีเน้นหัวพยัญชนะ ใช้ Google Earth และเขียนชื่อสีกำกับ
21	แก้ม	สิทธิชัย แจ่มแจ้ง	ป.2/2	ภาษาไทย	ปัญหา: เขียนหนังสือช้าและกดแรงมาก | วิธีรับมือ: ใช้ดินสอ 2B และยางจับดินสอแบบนิ่มช่วย
22	ตูน	อาทิตย์ บริบูรณ์	ป.3/1	คณิตศาสตร์, วิทยาศาสตร์	ปัญหา: เปรียบเทียบเศษส่วนไม่ได้ จำแนกหินดินแร่ไม่ได้ | วิธีรับมือ: ใช้สื่อเค้กจำลองสอนเศษส่วน และให้สัมผัสหินของจริง
23	เบล	กิตติพงศ์ วรเวช	ป.4/1	ภาษาอังกฤษ	ปัญหา: ไม่กล้าพูดเพราะนึกคำไม่ออก | วิธีรับมือ: ให้พูดคำศัพท์สั้นๆ และชมเชยทุกครั้งที่กล้าพูด
24	ปอนด์	ทนงศักดิ์ แสงสว่าง	ป.5/2	วิทยาศาสตร์, คณิตศาสตร์	ปัญหา: คำนวณหาความหนาแน่นไม่ได้ | วิธีรับมือ: อนุญาตให้ใช้เครื่องคิดเลขในการคำนวณวิทย์
25	นัท	นันทวัฒน์ ใจดี	ป.6/1	ภาษาไทย	ปัญหา: จับใจความสำคัญไม่ได้เลย | วิธีรับมือ: ใช้เทคนิคเพื่อนช่วยเพื่อน (Buddy) เล่าสรุปให้ฟัง
26	มอส	ประเสริฐ มีทรัพย์	ป.1/2	คณิตศาสตร์, สุขศึกษาฯ	ปัญหา: ลบเลขแบบยืมไม่ได้ และกระโดดขาเดียวไม่ได้ (การทรงตัว) | วิธีรับมือ: ใช้ตารางหลักสิบช่วยสอน และฝึกเดินทรงตัวบนเส้นตรง
27	แจ็ค	สมชาย มาดี	ป.2/1	ภาษาอังกฤษ, ภาษาไทย	ปัญหา: สับสน b/d และ ด/ค | วิธีรับมือ: ใช้เทคนิคกำปั้น (b like thumb up)
28	กิ๊ฟ	วิชัย รักษ์ดี	ป.3/2	ภาษาไทย	ปัญหา: สะกดคำแม่ก กา ผิดบ่อย | วิธีรับมือ: เล่นเกมบิงโกคำศัพท์แม่ ก กา
29	น้ำ	เฉลิมชัย ใจซื่อ	ป.4/1	คณิตศาสตร์, ภาษาอังกฤษ	ปัญหา: สับสนทศนิยม และจำคำศัพท์หมวดวันเดือนไม่ได้ | วิธีรับมือ: ใช้ไม้บรรทัดแสดงทศนิยม และร้องเพลง Days of the week
30	โฟน	บุญส่ง แซ่ตั้ง	ป.5/2	วิทยาศาสตร์	ปัญหา: ไม่เข้าใจเรื่องแรงเสียดทาน | วิธีรับมือ: ทดลองลากวัตถุบนพื้นผิวต่างกันให้เห็นจริง
31	เป้	อุดม คงกระพัน	ป.6/1	ภาษาไทย, สังคมศึกษาฯ	ปัญหา: เขียนเรียงความวกวน และจำลำดับเหตุการณ์ประวัติศาสตร์ไม่ได้ | วิธีรับมือ: ให้เขียนเป็นข้อๆ (Bullet point) และใช้เส้นเวลา (Timeline)
32	มายด์	จรัญ เรียนเก่ง	ป.1/1	ภาษาอังกฤษ, ศิลปะ	ปัญหา: จำ A-Z ไม่ครบ และวาดรูปคนมีส่วนประกอบไม่ครบ | วิธีรับมือ: ร้องเพลง ABC และให้เติมส่วนที่หายไปของภาพ
33	ออม	ชัชวาล วงศ์สวัสดิ์	ป.4/1	คณิตศาสตร์	ปัญหา: แก้โจทย์ปัญหา 2 ชั้นไม่ได้ | วิธีรับมือ: ขีดเส้นใต้สิ่งที่โจทย์ถามและสิ่งที่โจทย์บอก
34	แบงค์	ดวงพร รัตนจริยา	ป.6/2	ภาษาไทย, วิทยาศาสตร์	ปัญหา: อ่านจับใจความบทร้อยกรองไม่ได้ และจำแนกสารเคมีไม่ได้ | วิธีรับมือ: แปลบทร้อยกรองเป็นภาษาพูดปกติ และติดป้ายชื่อสารเคมีด้วยสี
35	มิลค์	พรพิมล ศิริสัมพันธ์	ป.6/1	วิทยาศาสตร์	ปัญหา: สับสนทิศทางและแผนที่ดาว | วิธีรับมือ: ใช้เข็มทิศจริงพาเดินสำรวจโรงเรียน
36	กันต์	กิตติเดช ทองประเสริฐ	ป.5/2	ภาษาอังกฤษ, คณิตศาสตร์	ปัญหา: แปลความหมายผิดบริบท และคำนวณพื้นที่ผิด | วิธีรับมือ: สอนศัพท์จากบริบทจริง และใช้ตารางกริดนับพื้นที่
37	เนย	สราวุฒิ รุ่งรัตนกุล	ป.3/1	คณิตศาสตร์, การงานอาชีพฯ	ปัญหา: จำสูตรคูณไม่ได้ และร้อยเข็มไม่ได้ | วิธีรับมือ: ใช้ตารางสูตรคูณวางบนโต๊ะ และใช้เข็มรูใหญ่/ไหมพรมฝึก
38	บี	เบญจมาศ มาเจริญ	ป.1/1	ภาษาไทย	ปัญหา: แยกอักษรสูง/กลาง/ต่ำ ไม่ได้ | วิธีรับมือ: ใช้สีแยกหมู่พยัญชนะ (ไตรยางศ์)
39	เต๋า	นราวิชญ์ ปัญญาดี	ป.2/2	ภาษาอังกฤษ, สุขศึกษาฯ	ปัญหา: เขียนศัพท์สลับหน้าหลัง (saw/was) และรับลูกบอลไม่ได้ | วิธีรับมือ: ฝึกสะกดคำทีละตัว และฝึกรับส่งบอลระยะใกล้
40	นุ๊ก	ปาริฉัตร รักษาสัตย์	ป.3/2	คณิตศาสตร์	ปัญหา: แยกรูปทรง 2 มิติ กับ 3 มิติไม่ออก | วิธีรับมือ: ให้จับของจริง (กล่อง, ลูกบอล) เทียบกับรูปวาด
41	เบส	พิสิษฐ์ เก่ง	ป.4/2	วิทยาศาสตร์, ภาษาไทย	ปัญหา: จัดกลุ่มสิ่งมีชีวิตผิด และเขียนคำพ้องเสียงผิด | วิธีรับมือ: ใช้เกมจัดหมวดหมู่ภาพสัตว์ และแต่งประโยคจากคำพ้อง
42	ดิว	กัญญารัตน์ เพิ่มสุข	ป.5/2	ภาษาไทย, สังคมศึกษาฯ	ปัญหา: ใช้คำบุพบทผิด (ใน/บน/ล่าง) และไม่เข้าใจวัฒนธรรมท้องถิ่น | วิธีรับมือ: สาธิตวางของตำแหน่งต่างๆ และพาไปดูพิพิธภัณฑ์ท้องถิ่น
43	กวาง	ปรีชา วงศ์สวัสดิ์	ป.3/1	คณิตศาสตร์, ภาษาอังกฤษ	ปัญหา: หารสั้นไม่ได้ และฟังคำสั่งภาษาอังกฤษไม่ออก | วิธีรับมือ: สอนวิธีหารยาวก่อน (เห็นภาพชัดกว่า) และใช้ท่าทางประกอบคำสั่ง (TPR)
44	ปลา	ศิริชัย รัตนจริยา	ป.2/1	ภาษาอังกฤษ, ศิลปะ	ปัญหา: ไม่เข้าใจ Tense และผสมสีไม่ได้ตามสั่ง | วิธีรับมือ: ใช้เส้นเวลา (Timeline) สอน Tense ง่ายๆ และให้ทดลองผสมสีน้ำเอง
45	นุ่น	ทิพวรรณ ศิริสัมพันธ์	ป.2/2	ภาษาไทย	ปัญหา: อ่านตะกุกตะกักมาก ขาดความมั่นใจ | วิธีรับมือ: ฝึกอ่านกับเพื่อนสนิท (Buddy Reading)
46	ตั้ม	เกรียงไกร ทองประเสริฐ	ป.1/1	คณิตศาสตร์, การงานอาชีพฯ	ปัญหา: เขียนเลขกลับด้าน (3, 7) และพับกระดาษไม่ตรงรอย | วิธีรับมือ: ลากนิ้วบนกระดาษทรายรูปตัวเลข และฝึกพับกระดาษตามเส้นประ
47	คิว	วราภรณ์ รุ่งรัตนกุล	ป.3/2	วิทยาศาสตร์	ปัญหา: สรุปผลการทดลองขัดแย้งกับข้อมูล | วิธีรับมือ: ใช้แบบเติมคำในช่องว่างเพื่อสรุปผล
48	เก่ง	สมชาย มาเจริญ	ป.6/1	ภาษาอังกฤษ, ภาษาไทย, สังคมศึกษาฯ	ปัญหา: อ่านคำควบกล้ำไม่ได้เลย และจำชื่อประเทศเพื่อนบ้านไม่ได้ | วิธีรับมือ: ฝึกออกเสียงหน้ากระจก และเล่นเกมต่อแผนที่อาเซียน
49	น้ำ	วีระ ปัญญาดี	ป.4/1	ภาษาไทย	ปัญหา: เขียนเรียงความไม่ได้ ประโยคไม่สมบูรณ์ | วิธีรับมือ: ให้เขียนโครงเรื่อง (Mind Map) ก่อนเขียนจริง
50	ฝน	วิชัย รักษาสัตย์	ป.5/2	คณิตศาสตร์, วิทยาศาสตร์	ปัญหา: คำนวณร้อยละไม่ได้ และคำนวณความเร็วไม่ได้ | วิธีรับมือ: ใช้เรื่องการลดราคาสินค้าในชีวิตจริง และดูหน้าปัดรถยนต์สอนเรื่องความเร็ว
51	เปิ้ล	ณัฐพล คงมั่น	ป.1/2	ภาษาไทย	ปัญหา: ลืมพยัญชนะตัวที่ไม่ค่อยได้ใช้ (ฆ, ฌ) | วิธีรับมือ: ติดโปสเตอร์พยัญชนะไทยไว้ที่โต๊ะ
52	ต่าย	ธนากร เพิ่มสุข	ป.2/2	วิทยาศาสตร์, ศิลปะ	ปัญหา: ไม่เข้าใจห่วงโซ่อาหาร และปั้นดินน้ำมันเป็นรูปทรงไม่ได้ | วิธีรับมือ: ใช้โมเดลสัตว์จำลองมาเรียงลำดับการกิน และฝึกปั้นรูปทรงพื้นฐาน (กลม, เหลี่ยม)
53	บาส	ชัชวาล แก้วมณี	ป.2/1	คณิตศาสตร์	ปัญหา: บวกเลขในใจไม่ได้ ต้องนับนิ้ว | วิธีรับมือ: อนุญาตให้นับนิ้วหรือใช้ตัวนับได้ ไม่ต้องห้าม
54	เอ็ม	ดวงพร จงดี	ป.3/2	ภาษาอังกฤษ, สุขศึกษาฯ	ปัญหา: จับใจความจากการฟังไม่ได้ และวิ่งซิกแซกไม่ได้ | วิธีรับมือ: ให้ฟังประโยคซ้ำ 2-3 รอบ และฝึกวิ่งอ้อมกรวยช้าๆ
55	กิ๊ฟ	พรพิมล ชื่นบาน	ป.5/1	ภาษาไทย, การงานอาชีพฯ	ปัญหา: ย่อความไม่ได้ และใช้คอมพิวเตอร์ (Mouse) ไม่คล่อง | วิธีรับมือ: ให้ขีดไฮไลท์ใจความสำคัญ และเล่นเกมคลิกเมาส์ฝึกความแม่นยำ
56	แนท	กิตติเดช งามวิไล	ป.3/1	คณิตศาสตร์, วิทยาศาสตร์	ปัญหา: แปลงหน่วยวัดผิด (ซม./เมตร) และอ่านเทอร์โมมิเตอร์ไม่เป็น | วิธีรับมือ: ใช้สายวัดจริงวัดของในห้อง และฝึกอ่านอุณหภูมิห้องจริง
57	บอล	สราวุฒิ วงศ์สวัสดิ์	ป.5/1	วิทยาศาสตร์, ภาษาอังกฤษ	ปัญหา: จำแนกสารไม่ได้ และเขียนศัพท์วิทย์ภาษาอังกฤษผิด | วิธีรับมือ: ทำสมุดภาพคำศัพท์วิทย์ (Picture Dictionary)
58	ออม	เบญจมาศ รัตนจริยา	ป.2/2	ภาษาไทย, ศิลปะ	ปัญหา: อ่านข้ามบรรทัด และไม่กล้าวาดรูป | วิธีรับมือ: ใช้ไม้บรรทัดทาบทีละบรรทัดขณะอ่าน และให้วาดรูปอิสระโดยไม่ตัดสินสวย/ไม่สวย
59	แบงค์	นราวิชญ์ ศิริสัมพันธ์	ป.5/2	คณิตศาสตร์	ปัญหา: แก้โจทย์สมการตัวแปรเดียวไม่ได้ | วิธีรับมือ: ใช้ตาชั่งจำลองสอนเรื่องสมดุลสมการ
60	มิลค์	ปาริฉัตร ทองประเสริฐ	ป.3/2	ภาษาอังกฤษ, สังคมศึกษาฯ	ปัญหา: เขียนวันเดือนปีภาษาอังกฤษผิด และไม่เข้าใจทิศในแผนที่ | วิธีรับมือ: ร้องเพลง Months of the year และแปะป้ายทิศจริงในห้องเรียน
61	กันต์	พิสิษฐ์ รุ่งรัตนกุล	ป.2/2	ภาษาไทย	ปัญหา: เขียนคำควบกล้ำตกหล่น (ความ-คาม) | วิธีรับมือ: ฝึกออกเสียงช้าๆ ชัดๆ เน้นตัวควบ
62	เนย	กัญญารัตน์ มาเจริญ	ป.5/1	วิทยาศาสตร์, คณิตศาสตร์	ปัญหา: ต่อวงจรไฟฟ้าไม่ได้ และคำนวณค่าไฟไม่เป็น | วิธีรับมือ: ให้ลองต่อวงจรจริง (ถ่าน-สายไฟ-หลอดไฟ)
63	บี	ปรีชา ปัญญาดี	ป.1/1	คณิตศาสตร์	ปัญหา: เรียงลำดับเลข 1-100 สับสน | วิธีรับมือ: ใช้ตารางร้อยช่อง (Hundred Chart)
64	เต๋า	ศิริชัย รักษาสัตย์	ป.3/2	ภาษาอังกฤษ, ภาษาไทย	ปัญหา: ใช้ is/am/are ผิด และแต่งประโยคภาษาไทยไม่รู้เรื่อง | วิธีรับมือ: ทำตารางสรุปการใช้ Verb to be และฝึกแต่งประโยคจากภาพ
65	นุ๊ก	ทิพวรรณ คงมั่น	ป.4/2	ภาษาไทย, การงานอาชีพฯ	ปัญหา: ใช้ไม้ยมกผิดที่ และพับผ้าไม่เรียบร้อย | วิธีรับมือ: สอนหลักการอ่านคำซ้ำ และสอนพับผ้าทีละขั้นตอน
66	เบส	เกรียงไกร เพิ่มสุข	ป.3/2	คณิตศาสตร์, ศิลปะ	ปัญหา: นับมุม/ด้านรูปทรงผิด และผสมสีโปสเตอร์ไม่ได้สีตามต้องการ | วิธีรับมือ: ให้ขีดฆ่ามุมที่นับแล้ว และทำวงล้อสีไว้ดูประกอบ
67	ดิว	วราภรณ์ วงศ์สวัสดิ์	ป.4/2	วิทยาศาสตร์	ปัญหา: อธิบายวัฏจักรน้ำไม่ได้ | วิธีรับมือ: วาดภาพวัฏจักรน้ำใส่ถุงซิปล็อคใส่น้ำแปะกระจก
68	กวาง	สมชาย รัตนจริยา	ป.4/1	ภาษาไทย, สังคมศึกษาฯ	ปัญหา: เขียนตัวการันต์ผิดตำแหน่ง และเรียงลำดับกษัตริย์ไม่ได้ | วิธีรับมือ: ทำบัตรคำคำที่มีการันต์ และร้องเพลงพระนามกษัตริย์
69	ปลา	วีระ ศิริสัมพันธ์	ป.2/1	ภาษาอังกฤษ, คณิตศาสตร์	ปัญหา: จำคำตรงข้าม (Big/Small) ไม่ได้ และวัดความยาวผิด | วิธีรับมือ: ใช้ของจริงเปรียบเทียบขนาด และสอนวิธีวางไม้บรรทัดเริ่มที่เลข 0
70	นุ่น	วิชัย ทองประเสริฐ	ป.2/2	คณิตศาสตร์	ปัญหา: ท่องสูตรคูณข้ามแม่ | วิธีรับมือ: ใช้ตารางสูตรคูณช่วย ไม่ต้องบังคับท่องปากเปล่า
71	ตั้ม	ณัฐพล รุ่งรัตนกุล	ป.1/1	ภาษาไทย	ปัญหา: อ่านไม่ออกเลยแม้แต่คำง่ายๆ | วิธีรับมือ: เน้นการฟังและดูรูปภาพแทนการอ่าน (Sight Words)
72	คิว	ธนากร มาเจริญ	ป.3/2	วิทยาศาสตร์, ภาษาไทย	ปัญหา: สับสนแรงผลัก/แรงดึง และสะกดคำแม่กดผิด (ด/ต/ถ/ท) | วิธีรับมือ: เล่นเกมชักเย่อ/ผลักรถ และรวบรวมคำแม่กดมาติดบอร์ด
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: piyaphatrattanarak
--

COPY public."user" (id, username, password) FROM stdin;
\.


--
-- Data for Name: user_access; Type: TABLE DATA; Schema: public; Owner: piyaphatrattanarak
--

COPY public.user_access (id, username, accessible_grade, accessible_student_id) FROM stdin;
24	patas	ป.4/1	\N
25	patas	ป.3/2	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: piyaphatrattanarak
--

COPY public.users (username, password, displayname, permission) FROM stdin;
admin	scrypt:32768:8:1$B2AHIaT2lO0TcC9S$63d2a8003c8e992f5c01861f2d0d854bd967296cb8da6927d35b11b50652f5a8609458024f13a17d702b55a421a1b38faac3a5b2a4777877ef6bb4191d3eeac0	Super Admin	Admin
patas	scrypt:32768:8:1$JsuplfG7bMKY1dO2$d8b793c0e2f8c822fbc1b5c2cef05acba251e4a36f353655fc789cdb4c5e35621c2c07e6f7758ea625afaeb96566fb75225bcf4dee27b2191e8a3cf2a098a2b6	User Test	User
\.


--
-- Name: students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: piyaphatrattanarak
--

SELECT pg_catalog.setval('public.students_id_seq', 72, true);


--
-- Name: user_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: piyaphatrattanarak
--

SELECT pg_catalog.setval('public.user_access_id_seq', 25, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: piyaphatrattanarak
--

SELECT pg_catalog.setval('public.user_id_seq', 1, false);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- Name: user_access user_access_pkey; Type: CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.user_access
    ADD CONSTRAINT user_access_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (username);


--
-- Name: user_access user_access_accessible_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.user_access
    ADD CONSTRAINT user_access_accessible_student_id_fkey FOREIGN KEY (accessible_student_id) REFERENCES public.students(id);


--
-- Name: user_access user_access_username_fkey; Type: FK CONSTRAINT; Schema: public; Owner: piyaphatrattanarak
--

ALTER TABLE ONLY public.user_access
    ADD CONSTRAINT user_access_username_fkey FOREIGN KEY (username) REFERENCES public.users(username);


--
-- PostgreSQL database dump complete
--

\unrestrict Gmf6WLoKLUmHHSzKFotdPca294bM51H7DHq6cYUTQCvoVATnO7cE9sQ8tkbjnYT

