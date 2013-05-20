<?php
/*
 * Copyright (c) 2010-2012, Contrail consortium.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms,
 * with or without modification, are permitted provided
 * that the following conditions are met:
 *
 *  1. Redistributions of source code must retain the
 *     above copyright notice, this list of conditions
 *     and the following disclaimer.
 *  2. Redistributions in binary form must reproduce
 *     the above copyright notice, this list of
 *     conditions and the following disclaimer in the
 *     documentation and/or other materials provided
 *     with the distribution.
 *  3. Neither the name of the Contrail consortium nor the
 *     names of its contributors may be used to endorse
 *     or promote products derived from this software
 *     without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
 * CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

require_module('application');
require_module('ui');

function DashboardApplicationUI(Application $application) {
	return new DashboardApplicationUI($application);
}

class DashboardApplicationUI {

	private $application;
	private $last = false;

	public function __construct(Application $application) {
		$this->application = $application;
	}

	public function setLast($last=true) {
		$this->last = $last;
		return $this;
	}

	private function renderStatistic($content) {
		return
			'<div class="statistic">'
				.'<div class="statcontent">'.$content.'</div>'
			.'</div>';
	}

    private function renderStats() {
        return $this->renderStatistic('<img class="deleteApplication-'.
            $this->application->getAID().'" src="images/remove.png" />');
    }

	private function renderTitle() {
		$title =
			'<a href="services.php?aid='.$this->application->getAID().'">'
			.$this->application->getName()
			.'</a>';

		return
			'<div class="title">'
				.$title
			.'</div>';
	}

	public function __toString() {
		$lastClass = $this->last ? 'last' : '';
		return
			'<tr class="service" id="service-'.$this->application->getAID().'">'
				.'<td class="wrapper '.$lastClass.'">'
					.'<div class="content">'
						.$this->renderTitle()
					.'</div>'
					.$this->renderStats()
					.'<div class="clear"></div>'
				.'</td>'
			.'</tr>';
	}

}
