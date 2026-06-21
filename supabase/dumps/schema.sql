--
-- PostgreSQL database dump
--

\restrict fweadqEQQ7luBWfZ3srhGqYJpiuCqgXbxAZJGqs3qXyBhh0GoXI9cdPhIwLCZlt

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.7 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    SET search_path TO 'pg_catalog', 'pg_temp'
    AS $$
begin
  new.updated_at = now();
  return new;
end;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.attempts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    question_id uuid NOT NULL,
    answered_correct boolean NOT NULL,
    time_taken_seconds integer NOT NULL,
    rated_knew_it boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    picked_answer jsonb,
    CONSTRAINT attempts_time_taken_seconds_check CHECK ((time_taken_seconds >= 0))
);


--
-- Name: bookmarks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bookmarks (
    user_id uuid NOT NULL,
    question_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.flags (
    user_id uuid NOT NULL,
    question_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: question_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_reports (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    question_id uuid NOT NULL,
    reason text NOT NULL,
    details text,
    resolved boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT question_reports_reason_check CHECK ((reason = ANY (ARRAY['contradiction'::text, 'incorrect'::text, 'unclear'::text, 'other'::text])))
);


--
-- Name: questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    topic_id uuid NOT NULL,
    body text NOT NULL,
    options jsonb,
    correct_answer jsonb NOT NULL,
    explanation text,
    regulation_clause text,
    difficulty smallint,
    variants_of uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    question_type text DEFAULT 'single_choice'::text NOT NULL,
    CONSTRAINT questions_difficulty_check CHECK (((difficulty >= 1) AND (difficulty <= 5))),
    CONSTRAINT questions_question_type_check CHECK ((question_type = ANY (ARRAY['single_choice'::text, 'multiple_select'::text, 'exact_value'::text])))
);


--
-- Name: readiness_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.readiness_snapshots (
    user_id uuid NOT NULL,
    date date NOT NULL,
    readiness_percent double precision NOT NULL,
    questions_seen integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    mode text NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    ended_at timestamp with time zone,
    score real,
    CONSTRAINT sessions_mode_check CHECK ((mode = ANY (ARRAY['study'::text, 'mock_exam'::text, 'diagnostic'::text]))),
    CONSTRAINT sessions_score_check CHECK (((score IS NULL) OR ((score >= (0)::double precision) AND (score <= (1)::double precision))))
);


--
-- Name: sm2_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sm2_state (
    user_id uuid NOT NULL,
    question_id uuid NOT NULL,
    easiness double precision DEFAULT 2.5 NOT NULL,
    interval_days integer DEFAULT 0 NOT NULL,
    repetitions integer DEFAULT 0 NOT NULL,
    due_date timestamp with time zone DEFAULT now() NOT NULL,
    last_reviewed_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT sm2_state_easiness_check CHECK ((easiness >= (1.3)::double precision)),
    CONSTRAINT sm2_state_interval_days_check CHECK ((interval_days >= 0)),
    CONSTRAINT sm2_state_repetitions_check CHECK ((repetitions >= 0))
);


--
-- Name: streaks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streaks (
    user_id uuid NOT NULL,
    current_streak integer DEFAULT 0 NOT NULL,
    longest_streak integer DEFAULT 0 NOT NULL,
    freeze_tokens integer DEFAULT 0 NOT NULL,
    last_active date,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT streaks_current_streak_check CHECK ((current_streak >= 0)),
    CONSTRAINT streaks_freeze_tokens_check CHECK ((freeze_tokens >= 0)),
    CONSTRAINT streaks_longest_streak_check CHECK ((longest_streak >= 0))
);


--
-- Name: topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topics (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    slug text NOT NULL,
    name text NOT NULL,
    brand_scope text NOT NULL,
    regulation_refs jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    weight smallint DEFAULT 1 NOT NULL,
    CONSTRAINT topics_weight_check CHECK (((weight >= 1) AND (weight <= 10)))
);


--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    id uuid NOT NULL,
    display_name text,
    exam_booked boolean DEFAULT false NOT NULL,
    exam_date date,
    daily_goal integer DEFAULT 20 NOT NULL,
    brand text DEFAULT 'sparkypass'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_profiles_daily_goal_check CHECK (((daily_goal >= 1) AND (daily_goal <= 500)))
);


--
-- Name: attempts attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT attempts_pkey PRIMARY KEY (id);


--
-- Name: bookmarks bookmarks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookmarks
    ADD CONSTRAINT bookmarks_pkey PRIMARY KEY (user_id, question_id);


--
-- Name: flags flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flags
    ADD CONSTRAINT flags_pkey PRIMARY KEY (user_id, question_id);


--
-- Name: question_reports question_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_reports
    ADD CONSTRAINT question_reports_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: readiness_snapshots readiness_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.readiness_snapshots
    ADD CONSTRAINT readiness_snapshots_pkey PRIMARY KEY (user_id, date);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sm2_state sm2_state_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sm2_state
    ADD CONSTRAINT sm2_state_pkey PRIMARY KEY (user_id, question_id);


--
-- Name: streaks streaks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_pkey PRIMARY KEY (user_id);


--
-- Name: topics topics_brand_scope_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_brand_scope_slug_key UNIQUE (brand_scope, slug);


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- Name: attempts_user_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX attempts_user_created_idx ON public.attempts USING btree (user_id, created_at DESC);


--
-- Name: attempts_user_question_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX attempts_user_question_idx ON public.attempts USING btree (user_id, question_id);


--
-- Name: question_reports_open_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX question_reports_open_idx ON public.question_reports USING btree (created_at DESC) WHERE (resolved = false);


--
-- Name: question_reports_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX question_reports_user_idx ON public.question_reports USING btree (user_id, created_at DESC);


--
-- Name: questions_topic_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX questions_topic_id_idx ON public.questions USING btree (topic_id);


--
-- Name: questions_variants_of_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX questions_variants_of_idx ON public.questions USING btree (variants_of) WHERE (variants_of IS NOT NULL);


--
-- Name: readiness_snapshots_user_date_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX readiness_snapshots_user_date_idx ON public.readiness_snapshots USING btree (user_id, date DESC);


--
-- Name: sessions_user_started_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX sessions_user_started_idx ON public.sessions USING btree (user_id, started_at DESC);


--
-- Name: sm2_state_user_due_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX sm2_state_user_due_idx ON public.sm2_state USING btree (user_id, due_date);


--
-- Name: topics_brand_scope_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX topics_brand_scope_idx ON public.topics USING btree (brand_scope);


--
-- Name: sm2_state sm2_state_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER sm2_state_set_updated_at BEFORE UPDATE ON public.sm2_state FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: streaks streaks_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER streaks_set_updated_at BEFORE UPDATE ON public.streaks FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: user_profiles user_profiles_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER user_profiles_set_updated_at BEFORE UPDATE ON public.user_profiles FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: attempts attempts_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT attempts_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: attempts attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: bookmarks bookmarks_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookmarks
    ADD CONSTRAINT bookmarks_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: bookmarks bookmarks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookmarks
    ADD CONSTRAINT bookmarks_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: flags flags_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flags
    ADD CONSTRAINT flags_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: flags flags_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.flags
    ADD CONSTRAINT flags_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: question_reports question_reports_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_reports
    ADD CONSTRAINT question_reports_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: question_reports question_reports_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_reports
    ADD CONSTRAINT question_reports_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: questions questions_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topics(id) ON DELETE CASCADE;


--
-- Name: questions questions_variants_of_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_variants_of_fkey FOREIGN KEY (variants_of) REFERENCES public.questions(id) ON DELETE SET NULL;


--
-- Name: readiness_snapshots readiness_snapshots_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.readiness_snapshots
    ADD CONSTRAINT readiness_snapshots_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: sm2_state sm2_state_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sm2_state
    ADD CONSTRAINT sm2_state_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: sm2_state sm2_state_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sm2_state
    ADD CONSTRAINT sm2_state_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: streaks streaks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streaks
    ADD CONSTRAINT streaks_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: attempts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.attempts ENABLE ROW LEVEL SECURITY;

--
-- Name: attempts attempts_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY attempts_self_insert ON public.attempts FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: attempts attempts_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY attempts_self_select ON public.attempts FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: bookmarks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;

--
-- Name: bookmarks bookmarks_self_delete; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY bookmarks_self_delete ON public.bookmarks FOR DELETE TO authenticated USING ((auth.uid() = user_id));


--
-- Name: bookmarks bookmarks_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY bookmarks_self_insert ON public.bookmarks FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: bookmarks bookmarks_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY bookmarks_self_select ON public.bookmarks FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: flags; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.flags ENABLE ROW LEVEL SECURITY;

--
-- Name: flags flags_self_delete; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY flags_self_delete ON public.flags FOR DELETE TO authenticated USING ((auth.uid() = user_id));


--
-- Name: flags flags_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY flags_self_insert ON public.flags FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: flags flags_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY flags_self_select ON public.flags FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: question_reports; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.question_reports ENABLE ROW LEVEL SECURITY;

--
-- Name: question_reports question_reports_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY question_reports_self_insert ON public.question_reports FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: question_reports question_reports_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY question_reports_self_select ON public.question_reports FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: questions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;

--
-- Name: questions questions_read_authenticated; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY questions_read_authenticated ON public.questions FOR SELECT TO authenticated USING (true);


--
-- Name: readiness_snapshots; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.readiness_snapshots ENABLE ROW LEVEL SECURITY;

--
-- Name: readiness_snapshots readiness_snapshots_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY readiness_snapshots_self_insert ON public.readiness_snapshots FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: readiness_snapshots readiness_snapshots_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY readiness_snapshots_self_select ON public.readiness_snapshots FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: readiness_snapshots readiness_snapshots_self_update; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY readiness_snapshots_self_update ON public.readiness_snapshots FOR UPDATE TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: sessions sessions_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sessions_self_insert ON public.sessions FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: sessions sessions_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sessions_self_select ON public.sessions FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: sessions sessions_self_update; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sessions_self_update ON public.sessions FOR UPDATE TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: sm2_state; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.sm2_state ENABLE ROW LEVEL SECURITY;

--
-- Name: sm2_state sm2_state_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sm2_state_self_insert ON public.sm2_state FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: sm2_state sm2_state_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sm2_state_self_select ON public.sm2_state FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: sm2_state sm2_state_self_update; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sm2_state_self_update ON public.sm2_state FOR UPDATE TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: streaks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.streaks ENABLE ROW LEVEL SECURITY;

--
-- Name: streaks streaks_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY streaks_self_insert ON public.streaks FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));


--
-- Name: streaks streaks_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY streaks_self_select ON public.streaks FOR SELECT TO authenticated USING ((auth.uid() = user_id));


--
-- Name: streaks streaks_self_update; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY streaks_self_update ON public.streaks FOR UPDATE TO authenticated USING ((auth.uid() = user_id)) WITH CHECK ((auth.uid() = user_id));


--
-- Name: topics; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.topics ENABLE ROW LEVEL SECURITY;

--
-- Name: topics topics_read_authenticated; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY topics_read_authenticated ON public.topics FOR SELECT TO authenticated USING (true);


--
-- Name: user_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: user_profiles user_profiles_self_insert; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_profiles_self_insert ON public.user_profiles FOR INSERT TO authenticated WITH CHECK ((auth.uid() = id));


--
-- Name: user_profiles user_profiles_self_select; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_profiles_self_select ON public.user_profiles FOR SELECT TO authenticated USING ((auth.uid() = id));


--
-- Name: user_profiles user_profiles_self_update; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY user_profiles_self_update ON public.user_profiles FOR UPDATE TO authenticated USING ((auth.uid() = id)) WITH CHECK ((auth.uid() = id));


--
-- PostgreSQL database dump complete
--

\unrestrict fweadqEQQ7luBWfZ3srhGqYJpiuCqgXbxAZJGqs3qXyBhh0GoXI9cdPhIwLCZlt

