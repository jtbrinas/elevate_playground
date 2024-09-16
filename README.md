<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a id="readme-top"></a>

<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->

<!-- PROJECT SHIELDS -->

<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[Contributors][contributors-url]
[Forks][forks-url]
[Stargazers][stars-url]
[Issues][issues-url]
[MIT License][license-url]
[LinkedIn][linkedin-url]

<!-- PROJECT LOGO -->

<br />
<div align="center">
  <a href="https://github.com/jtbrinas/elevate_playground.git">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Legal Hub Chatbot</h3>

<p align="center">
    Legal Assistant powered by Gemini
    <br />
    <a href="https://github.com/jtbrinas/elevate_playground.git"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/jtbrinas/elevate_playground.git">View Demo</a>
    ·
    <a href="https://github.com/jtbrinas/elevate_playground/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/jtbrinas/elevate_playground/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

This application is a simple chatbot designed to help explore the capabilities of Gemini in a legal context.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [LangChain](https://www.langchain.com/langchain)
* [LangGraph](https://langchain-ai.github.io/langgraph/)
* [Pinecone](https://www.pinecone.io/?utm_term=pinecone%20database&utm_campaign=Brand+-+US/Canada&utm_source=adwords&utm_medium=ppc&hsa_acc=3111363649&hsa_cam=16223687665&hsa_grp=133738612775&hsa_ad=582256510975&hsa_src=g&hsa_tgt=kwd-1628011569744&hsa_kw=pinecone%20database&hsa_mt=p&hsa_net=adwords&hsa_ver=3&gad_source=1&gclid=Cj0KCQjwrp-3BhDgARIsAEWJ6Sz7r4qVzWzbLSftCggFHTNYvZLJEPyfXn4l0L0vfmn7sYPGa0OVV9QaAgQEEALw_wcB)
* [Flask](https://flask.palletsprojects.com/en/3.0.x/)
* [Bootstrap][Bootstrap-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

To host the app locally, follow the steps below.

### Prerequisites

1. Install [Poetry](https://python-poetry.org/docs/) to help download dependencies

### Installation

1. Get the necessary keys:

* [Gemini API](https://ai.google.dev/gemini-api?gad_source=1&gclid=Cj0KCQjwrp-3BhDgARIsAEWJ6Swq_bYomTGkFNOxGD8XTlsvcWl3A2_l4RWSCMPmjiDyEICk6bkmRxYaAqFsEALw_wcB)
* [LangChain API](https://python.langchain.com/v0.1/docs/get_started/quickstart/)
* [Pinecone API](https://www.pinecone.io/?utm_term=pinecone%20database&utm_campaign=Brand+-+US/Canada&utm_source=adwords&utm_medium=ppc&hsa_acc=3111363649&hsa_cam=16223687665&hsa_grp=133738612775&hsa_ad=582256510975&hsa_src=g&hsa_tgt=kwd-1628011569744&hsa_kw=pinecone%20database&hsa_mt=p&hsa_net=adwords&hsa_ver=3&gad_source=1&gclid=Cj0KCQjwrp-3BhDgARIsAEWJ6SyueiB9lDFyOKqNYt5nNxx6hz4p06FxpM247-wJLaO9OeM6wLUm-i0aAulDEALw_wcB)
* Flask secret key: Below is one way to create a secret key

  ```python
  import secrets
  secret_key = secrets.token_hex(32)
  ```

2. Clone the repo
   ```sh
   git clone https://github.com/jtbrinas/elevate_playground.git
   ```
3. Put the necessary keys into a .env file
   ```sh
   GOOGLE_API_KEY=[YOUR GEMINI KEY HERE]
   LANGCHAIN_API_KEY=[YOUR LANGCHAIN KEY HERE]
   PINECONE_API_KEY=[YOUR PINECONE KEY HERE]
   FLASK_SECRET_KEY=[YOUR FLASK SECRET KEY HERE]
   ```
4. Install the necessary packages in the cloned repo
   ```sh
   poetry install
   ```
5. Activate the virtual environment
   ```sh
   poetry shell
   ```
6. Run app.py to host the app locally
   ```sh
   python elevate_playground/app.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

Currently, the chatbot has the usual conversational capabilities. Users can also upload pdf files to which are stored in your Pinecone database.
Then, the chatbot will be able to use that information to generate responses.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->

## Roadmap

- [ ] Separate user databases
- [ ] Allow for user to submit prompt and file at the same time
- [ ] Implement streaming for deployed version
- [ ] Explore possiblity of producing analytics
- [ ] Improve response quality
  - [ ] Incorporate metadata into database
  - [ ] Experiment with different prompting

See the [open issues](https://github.com/jtbrinas/elevate_playground/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/jtbrinas/elevate_playground/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=jtbrinas/elevate_playground" alt="contrib.rocks image" />
</a>

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

Jeremy Brinas - jt.brinas@gmail.com

Project Link: [https://github.com/jtbrinas/elevate_playground.git](https://github.com/jtbrinas/elevate_playground.git)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->

<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/jtbrinas/elevate_playground.svg?style=for-the-badge
[contributors-url]: https://github.com/jtbrinas/elevate_playground/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/jtbrinas/elevate_playground.svg?style=for-the-badge
[forks-url]: https://github.com/jtbrinas/elevate_playground/network/members
[stars-shield]: https://img.shields.io/github/stars/jtbrinas/elevate_playground.svg?style=for-the-badge
[stars-url]: https://github.com/jtbrinas/elevate_playground/stargazers
[issues-shield]: https://img.shields.io/github/issues/jtbrinas/elevate_playground.svg?style=for-the-badge
[issues-url]: https://github.com/jtbrinas/elevate_playground/issues
[license-shield]: https://img.shields.io/github/license/jtbrinas/elevate_playground.svg?style=for-the-badge
[license-url]: https://github.com/jtbrinas/elevate_playground/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/jeremy-brinas/
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com
