<!--.vitepress/theme/MyLayout.vue-->
<script setup>
import DefaultTheme from "vitepress/theme";

import AsideSponsors from "@theme/components/AsideSponsors.vue";
import BuyMeACoffee from "@theme/components/BuyMeACoffee.vue";

const { Layout } = DefaultTheme;
</script>

<template>
    <Layout>
        <!-- https://vitepress.dev/guide/extending-default-theme#layout-slots -->

        <template #aside-ads-before>
            <AsideSponsors />
        </template>

        <template #aside-bottom>
            <BuyMeACoffee />
        </template>
    </Layout>
</template>
